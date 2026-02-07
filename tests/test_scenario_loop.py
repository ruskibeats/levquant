"""Tests for kill-switch scenario loop and fear override behavior."""

from cli.run import run_engine
from scenarios.kill_switches import build_kill_switch_set, compute_fear_index
from scenarios.scenario_loop import (
    run_scenario,
    settlement_posture_from_fear,
)


def test_fear_index_zero_when_no_active_claimant_switches() -> None:
    switches = build_kill_switch_set([])
    assert compute_fear_index(switches) == 0.0


def test_fear_index_uses_max_active_claimant_severity() -> None:
    switches = build_kill_switch_set([
        "insurer_notified_of_fraud",  # 0.85
        "sra_investigation_open",    # 0.90
    ])
    assert compute_fear_index(switches) == 0.90


def test_override_behavior_thresholds() -> None:
    assert settlement_posture_from_fear(0.74) == "NORMAL"
    assert settlement_posture_from_fear(0.75) == "URGENT"
    assert settlement_posture_from_fear(0.90) == "FORCE"


def test_engine_values_not_mutated_by_kill_switch_overlay() -> None:
    base_state = {"SV1a": 0.38, "SV1b": 0.86, "SV1c": 0.75}

    engine_raw = run_engine(state=base_state)

    row = run_scenario(
        {
            "scenario_name": "overlay_check",
            "description": "Overlay should not mutate deterministic outputs.",
            "sv1a": 0.38,
            "sv1b": 0.86,
            "sv1c": 0.75,
            "active_kill_switch_names": ["sra_investigation_open"],
        }
    )

    assert row["UPLS"] == engine_raw["scores"]["upls"]
    assert row["engine_decision"] == engine_raw["evaluation"]["decision"]
    assert row["engine_confidence"] == engine_raw["evaluation"]["confidence"]


def test_force_settlement_override_applies_when_fear_high() -> None:
    row = run_scenario(
        {
            "scenario_name": "force_case",
            "description": "High fear should force settlement posture.",
            "sv1a": 0.38,
            "sv1b": 0.86,
            "sv1c": 0.75,
            "active_kill_switch_names": ["defence_nullity_confirmed"],  # severity 1.00
        }
    )

    assert row["FEAR_INDEX"] == 1.0
    assert row["settlement_posture"] == "FORCE"
