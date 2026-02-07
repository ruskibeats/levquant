"""Explicit scenario loop with kill-switch fear overlays.

This module introduces a finite (non-random) scenario analysis layer.
It consumes deterministic engine outputs via cli.run.run_engine() and
applies post-scoring fear/settlement posture logic without changing UPLS.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Literal, TypedDict

# Add project root to path for package imports when run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.run import run_engine
from scenarios.kill_switches import (
    KillSwitch,
    build_kill_switch_set,
    compute_fear_index,
)


SettlementPosture = Literal["NORMAL", "URGENT", "FORCE"]


class ScenarioSpec(TypedDict):
    """Scenario world definition."""

    scenario_name: str
    description: str
    sv1a: float
    sv1b: float
    sv1c: float
    active_kill_switch_names: List[str]


class ScenarioRow(TypedDict):
    """Output row for decision + fear matrix."""

    scenario_name: str
    SV1a: float
    SV1b: float
    SV1c: float
    engine_decision: str
    engine_confidence: str
    UPLS: float
    FEAR_INDEX: float
    settlement_posture: str
    active_kill_switches: str
    short_explanation: str


SCENARIOS: List[ScenarioSpec] = [
    {
        "scenario_name": "baseline_control",
        "description": "Current baseline inputs with no kill-switch activation.",
        "sv1a": 0.38,
        "sv1b": 0.86,
        "sv1c": 0.75,
        "active_kill_switch_names": [],
    },
    {
        "scenario_name": "procedural_softening",
        "description": "Slight procedural degradation but no external pressure flags.",
        "sv1a": 0.38,
        "sv1b": 0.76,
        "sv1c": 0.75,
        "active_kill_switch_names": [],
    },
    {
        "scenario_name": "insurer_notice",
        "description": "Insurer receives fraud notification.",
        "sv1a": 0.38,
        "sv1b": 0.86,
        "sv1c": 0.75,
        "active_kill_switch_names": ["insurer_notified_of_fraud"],
    },
    {
        "scenario_name": "reserving_rights",
        "description": "Insurer reserves rights while merits remain baseline.",
        "sv1a": 0.38,
        "sv1b": 0.86,
        "sv1c": 0.75,
        "active_kill_switch_names": ["insurer_reserves_rights"],
    },
    {
        "scenario_name": "regulatory_open",
        "description": "Regulatory investigation opens alongside baseline economics.",
        "sv1a": 0.38,
        "sv1b": 0.82,
        "sv1c": 0.75,
        "active_kill_switch_names": ["sra_investigation_open"],
    },
    {
        "scenario_name": "metadata_validated",
        "description": "Police metadata validation supports evidential integrity.",
        "sv1a": 0.42,
        "sv1b": 0.82,
        "sv1c": 0.75,
        "active_kill_switch_names": ["police_metadata_validated"],
    },
    {
        "scenario_name": "override_admitted",
        "description": "Administrative override admitted on-record.",
        "sv1a": 0.35,
        "sv1b": 0.80,
        "sv1c": 0.75,
        "active_kill_switch_names": ["administrative_override_admitted"],
    },
    {
        "scenario_name": "shadow_director",
        "description": "Shadow director evidence established.",
        "sv1a": 0.35,
        "sv1b": 0.78,
        "sv1c": 0.75,
        "active_kill_switch_names": ["shadow_director_established"],
    },
    {
        "scenario_name": "nullity_confirmed",
        "description": "Defence nullity is confirmed by documentary record.",
        "sv1a": 0.32,
        "sv1b": 0.76,
        "sv1c": 0.75,
        "active_kill_switch_names": ["defence_nullity_confirmed"],
    },
    {
        "scenario_name": "compound_insurer_regulator",
        "description": "Insurer notification + SRA investigation both active.",
        "sv1a": 0.35,
        "sv1b": 0.78,
        "sv1c": 0.75,
        "active_kill_switch_names": [
            "insurer_notified_of_fraud",
            "sra_investigation_open",
        ],
    },
    {
        "scenario_name": "compound_highest_fear",
        "description": "Multiple severe switches active including nullity and override.",
        "sv1a": 0.30,
        "sv1b": 0.72,
        "sv1c": 0.75,
        "active_kill_switch_names": [
            "defence_nullity_confirmed",
            "administrative_override_admitted",
            "insurer_reserves_rights",
        ],
    },
    {
        "scenario_name": "economic_stress_no_switch",
        "description": "Economic stress only; verifies no fear override without switches.",
        "sv1a": 0.28,
        "sv1b": 0.64,
        "sv1c": 0.60,
        "active_kill_switch_names": [],
    },
]


def settlement_posture_from_fear(fear_index: float) -> SettlementPosture:
    """Map FEAR_INDEX into settlement posture bucket."""
    if fear_index >= 0.90:
        return "FORCE"
    if fear_index >= 0.75:
        return "URGENT"
    return "NORMAL"


def short_explanation(engine_decision: str, settlement_posture: SettlementPosture, fear_index: float) -> str:
    """Create concise explanation for matrix row."""
    if settlement_posture == "FORCE":
        return f"FEAR_INDEX {fear_index:.2f} >= 0.90; force settlement despite engine={engine_decision}."
    if settlement_posture == "URGENT":
        return f"FEAR_INDEX {fear_index:.2f} >= 0.75; urgent settlement overlay on engine={engine_decision}."
    return f"FEAR_INDEX {fear_index:.2f} below override thresholds; retain engine={engine_decision}."


def run_scenario(spec: ScenarioSpec) -> ScenarioRow:
    """Run single explicit scenario and produce matrix row."""
    state = {"SV1a": spec["sv1a"], "SV1b": spec["sv1b"], "SV1c": spec["sv1c"]}
    engine_output = run_engine(state=state)

    engine_decision = engine_output["evaluation"]["decision"]
    engine_confidence = engine_output["evaluation"]["confidence"]
    upls = engine_output["scores"]["upls"]

    kill_switches: List[KillSwitch] = build_kill_switch_set(spec["active_kill_switch_names"])
    fear_index = compute_fear_index(kill_switches)
    posture = settlement_posture_from_fear(fear_index)

    active_names = [ks["name"] for ks in kill_switches if ks["active"]]
    active_csv = ",".join(active_names)

    return {
        "scenario_name": spec["scenario_name"],
        "SV1a": spec["sv1a"],
        "SV1b": spec["sv1b"],
        "SV1c": spec["sv1c"],
        "engine_decision": engine_decision,
        "engine_confidence": engine_confidence,
        "UPLS": upls,
        "FEAR_INDEX": round(fear_index, 3),
        "settlement_posture": posture,
        "active_kill_switches": active_csv,
        "short_explanation": short_explanation(engine_decision, posture, fear_index),
    }


def run_scenario_loop(scenarios: List[ScenarioSpec] | None = None) -> List[ScenarioRow]:
    """Run finite scenario loop (non-Monte Carlo)."""
    if scenarios is None:
        scenarios = SCENARIOS
    return [run_scenario(spec) for spec in scenarios]


def write_outputs(rows: List[ScenarioRow], output_dir: Path) -> None:
    """Write scenario decision + fear matrix to CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "scenario_matrix.csv"
    json_path = output_dir / "scenario_matrix.json"

    columns = [
        "scenario_name",
        "SV1a",
        "SV1b",
        "SV1c",
        "engine_decision",
        "engine_confidence",
        "UPLS",
        "FEAR_INDEX",
        "settlement_posture",
        "active_kill_switches",
        "short_explanation",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def print_console_summary(rows: List[ScenarioRow]) -> None:
    """Print required scenario posture summary."""
    posture_counts = {"NORMAL": 0, "URGENT": 0, "FORCE": 0}
    for row in rows:
        posture_counts[row["settlement_posture"]] += 1

    top = max(rows, key=lambda r: r["FEAR_INDEX"])
    hold_overrides = [
        r
        for r in rows
        if r["engine_decision"] == "HOLD" and r["settlement_posture"] in {"URGENT", "FORCE"}
    ]

    print("=" * 70)
    print("SCENARIO DECISION + FEAR MATRIX SUMMARY")
    print("=" * 70)
    print()
    print("Settlement posture counts:")
    for k in ["NORMAL", "URGENT", "FORCE"]:
        print(f"  {k:7s}: {posture_counts[k]}")
    print()
    print("Highest FEAR_INDEX scenario:")
    print(f"  {top['scenario_name']}: FEAR_INDEX={top['FEAR_INDEX']:.3f}, posture={top['settlement_posture']}")
    print()
    print("Engine HOLD but FEAR override scenarios:")
    if not hold_overrides:
        print("  (none)")
    else:
        for row in hold_overrides:
            print(
                f"  {row['scenario_name']}: engine={row['engine_decision']}, "
                f"fear={row['FEAR_INDEX']:.3f}, posture={row['settlement_posture']}"
            )


def main() -> None:
    """Run explicit scenario loop and emit matrix artifacts."""
    rows = run_scenario_loop()
    write_outputs(rows, Path("outputs"))
    print_console_summary(rows)


if __name__ == "__main__":
    main()
