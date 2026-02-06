# Procedural Leverage Engine

This project computes a Unified Procedural Leverage Score (UPLS) to support internal decision-making in commercial dispute settlement negotiations.

It is a deterministic, scenario-driven model intended as a decision aid, not a decision-maker.

**UPLS Definition**: UPLS is a scalar in the range [0.0, 1.0] representing the weighted aggregate of procedural, conduct, and cost leverage factors, intended to approximate relative settlement pressure rather than probability of success.

## What It Does

The engine calculates procedural leverage scores based on three key vectors:

- **SV1a**: Claim validity strength (0.0 to 1.0)
- **SV1b**: Procedural advantage (0.0 to 1.0)
- **SV1c**: Cost asymmetry (0.0 to 1.0)

These inputs are combined into a single UPLS score using weighted formulas, which is then used to determine recommended actions (ACCEPT, COUNTER, REJECT, or HOLD).

## Assumptions

1. **Deterministic Model**: All inputs produce the same outputs. No probabilistic elements.
2. **Bounded Inputs**: All SV values must be in the range [0.0, 1.0].
3. **Weighted Importance**: These weights are fixed by design to reflect a baseline commercial-litigation risk profile. Claim validity (40%), procedural advantage (35%), and cost asymmetry (25%) constitute the core weighting. Alternative weightings may be explored via scenario sweeps, but the core engine remains invariant.
4. **Linear Computation**: Linear aggregation at the scoring layer. Non-linear decision thresholds may exist only in the evaluation layer.
5. **No External Dependencies**: Pure Python implementation with no framework requirements, to ensure auditability, reproducibility, and long-term stability under refactor or environment changes.

## Non-Goals

This engine does not:
- Predict judicial outcomes
- Estimate probabilities of liability or quantum
- Model opponent psychology or negotiation tactics
- Replace legal advice or forensic analysis

It exists solely to impose disciplined structure on settlement leverage assessment.

## How to Run

### Basic Execution

```bash
cd procedural_leverage_engine
python -m cli.run
```

This will:
1. Load the current case state from `engine/state.py`
2. Compute UPLS and tripwire scores
3. Generate a decision recommendation
4. Print a formatted summary to stdout

### Running Tests

```bash
cd procedural_leverage_engine
python -m pytest tests/test_scoring.py -v
```

The test suite locks the scoring outputs. If tests fail, the economics have changed and require explicit review.

## Project Structure

```
procedural_leverage_engine/
├── README.md
├── engine/
│   ├── scoring.py          # UPLS math (immutable, version-locked)
│   ├── state.py            # current case inputs
│   ├── evaluation.py       # accept / counter / reject logic
│   └── interpretation.py   # human-readable labels
├── scenarios/
│   ├── sweeps.py           # SV sweeps / what-ifs
│   └── presets.py          # named scenarios
├── cli/
│   └── run.py              # command-line entry point
└── tests/
    └── test_scoring.py     # output locks
```

## Important Notes

- **`engine/scoring.py` is version-locked**: Changes here modify the economics and require test updates.
- **State is explicit**: Current inputs are in `engine/state.py`, not in external files.
- **No I/O in scoring**: The math functions are pure and deterministic.
- **Tests are locks**: `test_scoring.py` prevents unintended changes to calculations.

## Design Principles

1. **Pure functions first** – no side effects
2. **Math is immutable** – the scoring logic never mutates state
3. **State is explicit** – no hidden globals
4. **Readable > clever** – this is decision support, not a Kaggle entry
5. **One responsibility per file**