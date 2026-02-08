"""Deterministic scenario pricing for dashboard tables and exports."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .monetary import build_pricing
from .schemas import (
    KillSwitchInputs,
    MonetaryInputs,
    ProceduralInputs,
    ScenarioResult,
    ValidationResult,
)


def _named_scenarios() -> dict[str, dict[str, float]]:
    return {
        "baseline": {"SV1a": 0.38, "SV1b": 0.86, "SV1c": 0.75},
        "authority_collapse": {"SV1a": 0.15, "SV1b": 0.86, "SV1c": 0.75},
        "cost_spike": {"SV1a": 0.38, "SV1b": 0.86, "SV1c": 0.95},
        "procedural_dominance": {"SV1a": 0.38, "SV1b": 0.95, "SV1c": 0.75},
        "everything_breaks": {"SV1a": 0.15, "SV1b": 0.20, "SV1c": 0.25},
        "optimal_leverage": {"SV1a": 0.95, "SV1b": 0.95, "SV1c": 0.95},
    }


def build_scenario_table(
    money: MonetaryInputs,
    kill: KillSwitchInputs,
    fear_override: float | None = None,
    extra_scenarios: dict[str, dict[str, float]] | None = None,
) -> list[ScenarioResult]:
    scenarios = _named_scenarios()
    if extra_scenarios:
        scenarios.update(extra_scenarios)

    rows: list[ScenarioResult] = []
    for name, state in scenarios.items():
        proc = ProceduralInputs(**state)
        priced = build_pricing(proc=proc, money=money, kill_switches=kill, fear_override=fear_override)
        engine = priced["engine"]
        corridor = priced["corridor"]
        rows.append(
            ScenarioResult(
                scenario=name,
                sv1a=proc.SV1a,
                sv1b=proc.SV1b,
                sv1c=proc.SV1c,
                upls=engine.upls,
                decision=engine.decision,
                tripwire=engine.tripwire,
                floor_gbp=corridor.floor_gbp,
                target_gbp=corridor.target_gbp,
                ceiling_gbp=corridor.ceiling_gbp,
                kill_switches_active=priced["kill_switches_active"],
                fear_index=priced["fear_index"],
                settlement_posture=priced["posture"],
            )
        )
    return rows


def export_scenario_matrix(rows: list[ScenarioResult], out_dir: str | Path = "outputs") -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "pricing_matrix.json"
    csv_path = out / "pricing_matrix.csv"

    payload = [r.model_dump() for r in rows]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    pd.DataFrame(payload).to_csv(csv_path, index=False)
    return json_path, csv_path


def build_heatmap_dataframe(
    money: MonetaryInputs,
    kill: KillSwitchInputs,
    fixed_sv1c: float,
    fear_override: float | None = None,
) -> pd.DataFrame:
    sv1a_grid = [0.15, 0.22, 0.28, 0.32, 0.35, 0.38, 0.42, 0.46, 0.50, 0.56, 0.65]
    sv1b_grid = [0.50, 0.58, 0.64, 0.70, 0.76, 0.82, 0.86, 0.90, 0.96]
    rows = []
    for sv1a in sv1a_grid:
        for sv1b in sv1b_grid:
            priced = build_pricing(
                proc=ProceduralInputs(SV1a=sv1a, SV1b=sv1b, SV1c=fixed_sv1c),
                money=money,
                kill_switches=kill,
                fear_override=fear_override,
            )
            engine = priced["engine"]
            corridor = priced["corridor"]
            rows.append(
                {
                    "SV1a": sv1a,
                    "SV1b": sv1b,
                    "SV1c": fixed_sv1c,
                    "upls": engine.upls,
                    "tripwire": engine.tripwire,
                    "decision": engine.decision,
                    "posture": priced["posture"],
                    "target_gbp": corridor.target_gbp,
                }
            )
    return pd.DataFrame(rows)


def run_validation_battery(
    proc: ProceduralInputs,
    money: MonetaryInputs,
    kill: KillSwitchInputs,
    fear_override: float | None = None,
) -> list[ValidationResult]:
    first = build_pricing(proc=proc, money=money, kill_switches=kill, fear_override=fear_override)
    second = build_pricing(proc=proc, money=money, kill_switches=kill, fear_override=fear_override)

    c1 = first["corridor"]
    posture = first["posture"]
    fear = first["fear_index"]
    trip = first["engine"].tripwire

    expected_posture = "FORCE" if fear >= 0.9 or trip >= 8.5 else "URGENT" if fear >= 0.75 or trip >= 7.5 else "NORMAL"

    checks = [
        ValidationResult(
            name="Deterministic replay",
            passed=(first["engine"].upls == second["engine"].upls and first["corridor"].target_gbp == second["corridor"].target_gbp),
            expected="Identical UPLS/target across repeated runs",
            actual=f"UPLS={first['engine'].upls:.3f}/{second['engine'].upls:.3f}, target={first['corridor'].target_gbp}/{second['corridor'].target_gbp}",
            rationale="No randomness in pricing path unless explicitly introduced",
            deviation_flag=False,
        ),
        ValidationResult(
            name="Corridor monotonicity",
            passed=(c1.floor_gbp <= c1.base_case_gbp <= c1.target_gbp <= c1.ceiling_gbp),
            expected="floor <= base_case <= target <= ceiling",
            actual=f"{c1.floor_gbp} <= {c1.base_case_gbp} <= {c1.target_gbp} <= {c1.ceiling_gbp}",
            rationale="Settlement corridor should be ordered and auditable",
            deviation_flag=False,
        ),
        ValidationResult(
            name="Input bounds",
            passed=(0 <= proc.SV1a <= 1 and 0 <= proc.SV1b <= 1 and 0 <= proc.SV1c <= 1),
            expected="SV inputs within [0,1]",
            actual=f"SV1a={proc.SV1a}, SV1b={proc.SV1b}, SV1c={proc.SV1c}",
            rationale="Engine contract requires bounded vectors",
            deviation_flag=False,
        ),
        ValidationResult(
            name="Posture threshold consistency",
            passed=(posture == expected_posture),
            expected=f"posture={expected_posture}",
            actual=f"posture={posture}, fear={fear:.2f}, tripwire={trip:.2f}",
            rationale="Fear/tripwire rules must map consistently to NORMAL/URGENT/FORCE",
            deviation_flag=False,
        ),
    ]

    return checks
