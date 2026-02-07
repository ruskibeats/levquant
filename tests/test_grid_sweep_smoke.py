"""Smoke tests for SV grid sweep tooling."""

from run_sv_grid_sweep import run_grid_sweep


def test_grid_sweep_smoke_reduced_grid():
    """Reduced 2x2x1 grid should return valid deterministic rows."""
    sv1a = [0.38, 0.50]
    sv1b = [0.70, 0.86]
    sv1c = [0.75]

    rows = run_grid_sweep(sv1a, sv1b, sv1c)

    # row count
    assert len(rows) == 4

    # required columns
    required = {
        "SV1a",
        "SV1b",
        "SV1c",
        "upls",
        "tripwire",
        "decision",
        "confidence",
        "tripwire_triggered",
    }

    for row in rows:
        assert required.issubset(row.keys())
        assert 0.0 <= row["upls"] <= 1.0
        assert row["decision"] in {"ACCEPT", "COUNTER", "REJECT", "HOLD"}
