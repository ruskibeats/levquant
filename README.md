# Procedural Leverage Engine

[![CI](https://github.com/ruskibeats/levquant/workflows/CI/badge.svg)](https://github.com/ruskibeats/levquant/actions)

This project computes a Unified Procedural Leverage Score (UPLS) to support internal decision-making in commercial dispute settlement negotiations.

It is a deterministic, scenario-driven model intended as a decision aid, not a decision-maker.

**UPLS Definition**: UPLS is a scalar in the range [0.0, 1.0] representing the weighted aggregate of procedural, conduct, and cost leverage factors, intended to approximate relative settlement pressure rather than probability of success.

## Installation

### From Source

```bash
cd procedural_leverage_engine
pip install -e .
```

This installs the `ple` command-line tool:

```bash
ple  # equivalent to python -m cli.run
ple --json  # JSON output
```

### Development Installation

```bash
cd procedural_leverage_engine
pip install -e ".[dev]"
```

This includes pytest, black, and ruff for development and testing.

## Decision Support Dashboard (Production Analytical Layer)

Run the dashboard:

```bash
cd procedural_leverage_engine
streamlit run web/dashboard.py
```

Architecture boundary:

- `engine/` = deterministic scoring truth (unchanged)
- `decision_support/` = monetary translation, scenarios, validation, audit metadata
- `web/` = presentation layer (Streamlit + Plotly)

### Evidence Exports

From the dashboard Export panel you can:

- Export full run JSON (engine + pricing + assumptions + audit hash)
- Export court-safe PDF summary
- Save scenario matrix to:
  - `outputs/pricing_matrix.json`
  - `outputs/pricing_matrix.csv`

### Pricing Assumptions Disclaimer

GBP corridor outputs are **decision-support assumptions**, not legal valuation facts.
They are deterministic transforms of:

1. Engine outputs (`UPLS`, `decision`, `tripwire`) via `cli.run.run_engine(...)`
2. Explicit monetary inputs and switch toggles
3. Published multipliers shown in the Assumptions & Audit panel

No commercial assumption is embedded in `/engine`.

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

### Basic Execution (Human-Readable Output)

```bash
cd procedural_leverage_engine
python -m cli.run
```

This will:
1. Load the current case state from `engine/state.py`
2. Compute UPLS and tripwire scores
3. Generate a decision recommendation
4. Print a formatted summary to stdout

Example output:
```
============================================================
PROCEDURAL LEVERAGE ENGINE - CASE ANALYSIS
============================================================

INPUTS:
  SV1a (Claim Validity): 0.38
  SV1b (Procedural Advantage): 0.86
  SV1c (Cost Asymmetry): 0.75

SCORES:
  UPLS: 0.641
  Tripwire: 6.41

DECISION:
  Action: HOLD
  Confidence: Moderate
  Tripwire Triggered: No

INTERPRETATION:
  Moderate procedural leverage - routine dispute parameters

============================================================
```

### JSON Output (Machine-Readable)

```bash
cd procedural_leverage_engine
python -m cli.run --json
# or
python -m cli.run -j
```

This outputs a deterministic JSON schema for automation, pipelines, and integrations:

```json
{
  "inputs": {
    "SV1a": 0.38,
    "SV1b": 0.86,
    "SV1c": 0.75
  },
  "scores": {
    "upls": 0.641,
    "tripwire": 6.41
  },
  "evaluation": {
    "decision": "HOLD",
    "confidence": "Moderate",
    "tripwire_triggered": false,
    "upls_value": 0.641,
    "tripwire_value": 6.41
  },
  "interpretation": {
    "leverage_position": "Moderate procedural leverage - routine dispute parameters",
    "decision_explanation": "Model indicates maintaining position is appropriate given current leverage posture.",
    "tripwire_status": "Caution zone - monitor for procedural changes",
    "confidence_explanation": "Model indicates moderate confidence in current leverage assessment."
  },
  "version": "1.0"
}
```

### Command-Line Help

```bash
python -m cli.run --help
```

This displays usage information and available flags.

### Running Tests

```bash
cd procedural_leverage_engine
python -m pytest tests/ -v
```

The test suite locks all core outputs (scoring, evaluation, interpretation, CLI). If tests fail, the economics or contracts have changed and require explicit review.

Test coverage:
- `tests/test_scoring.py` - 7 tests (baseline outputs)
- `tests/test_evaluation.py` - 26 tests (thresholds, confidence, tripwire)
- `tests/test_interpretation.py` - 30 tests (language, contracts, formatting)
- `tests/test_cli.py` - 11 tests (human/JSON modes, schema validation)

Total: 74 tests

## Grid Sweep

Run a deterministic SV terrain sweep across a fixed 495-point grid:

```bash
cd procedural_leverage_engine
python run_sv_grid_sweep.py
```

This generates:

- `outputs/grid/grid_all.csv`
- `outputs/grid/grid_sv1c_0.45.csv` ... `grid_sv1c_0.95.csv`
- `outputs/grid/plots/heatmap_upls_sv1c_<value>.png`
- `outputs/grid/plots/heatmap_decision_sv1c_<value>.png`

The script also prints:

- total grid points
- decision counts per SV1c slice
- min/max/mean UPLS per slice
- detected 4-neighbour decision cliff transitions

## Probabilistic Extensions

The `/probabilistic` directory provides uncertainty quantification and scenario exploration on top of the deterministic core engine. It does not modify or replace the core engine—it consumes it via JSON output or the `run_engine()` function.

**Critical Design Principle**: NEVER import from `/engine` directly. Always consume via CLI JSON output or `run_engine()` function.

### What It Does

The probabilistic layer provides:
- **Uncertainty quantification** (Monte Carlo distributions)
- **Scenario exploration** (stress testing, what-if analysis)
- **Posterior updates** (Bayesian learning from outcomes, optional)

These are **orthogonal concerns** to the deterministic engine. The deterministic engine provides leverage posture and decision recommendations. The probabilistic layer quantifies uncertainty around those estimates.

### Architecture Boundary

**Allowed**:
- Consume CLI JSON output via `probabilistic/adapters.py`
- Call `run_engine()` from CLI layer
- Use Pydantic schemas to validate JSON contracts

**Forbidden**:
- Import from `/engine` directly
- Modify deterministic math or thresholds
- Mix probabilistic and deterministic logic in same file

### Usage Examples

**Monte Carlo Sampling** (quantify uncertainty):
```python
from probabilistic.monte_carlo import NormalDistribution, monte_carlo_sample
from probabilistic.adapters import run_deterministic_engine

# Define distributions for SV parameters
sv1a_dist = NormalDistribution(mean=0.38, std=0.05)
sv1b_dist = NormalDistribution(mean=0.86, std=0.03)
sv1c_dist = NormalDistribution(mean=0.75, std=0.08)

# Sample 10,000 scenarios
result = monte_carlo_sample(
    n_samples=10000,
    sv1a_dist=sv1a_dist,
    sv1b_dist=sv1b_dist,
    sv1c_dist=sv1c_dist
)

# Access decision proportions
print(result.decision_proportions)
# {'ACCEPT': 0.23, 'COUNTER': 0.45, 'HOLD': 0.27, 'REJECT': 0.05}
```

**Stress Scenarios** (what-if analysis):
```python
from probabilistic.scenarios import run_scenario

# Run predefined stress test
result = run_scenario('cost_spike')
print(result.scenario_name)  # 'cost_spike'
print(result.output.evaluation.decision)  # 'HOLD'
print(result.description)  # 'Maximum cost asymmetry - worst-case cost exposure'
```

**Custom Scenarios** (tailored what-ifs):
```python
from probabilistic.scenarios import run_custom_scenario

result = run_custom_scenario(
    scenario_name='aggressive_offer',
    sv1a=0.7,
    sv1b=0.9,
    sv1c=0.4,
    description='Opponent makes aggressive offer'
)
print(result.output.evaluation.decision)  # 'ACCEPT' (or appropriate decision)
```

### Non-Goals (Probabilistic Layer)

The probabilistic extensions do not:
- Replace the deterministic engine
- Modify `/engine` in any way
- Predict judicial outcomes (liability, quantum)
- Model opponent psychology or negotiation tactics
- Provide probability-of-success estimates

They exist solely to:
- Quantify uncertainty around deterministic leverage estimates
- Explore scenario space systematically
- Provide structured output for higher-order decision systems

### Directory Structure

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
├── probabilistic/            # v2.0-skeleton (structure only, not implemented)
│   ├── README.md             # architecture doc (NEVER import /engine)
│   ├── __init__.py           # validation helper
│   ├── schemas.py            # Pydantic JSON models
│   ├── adapters.py           # CLI wrapper
│   ├── monte_carlo.py        # SV sampling (skeleton)
│   ├── scenarios.py           # named presets
│   └── tests/
│       ├── __init__.py
│       ├── test_monte_carlo.py  # distribution tests
│       └── test_scenarios.py    # preset validation
└── tests/
    ├── test_scoring.py     # output locks
    ├── test_evaluation.py  # evaluation tests
    ├── test_interpretation.py  # interpretation tests
    └── test_cli.py         # CLI tests
```

### Safety Guarantees

- **Zero Core Pollution**: Probabilistic code never imports from `/engine`
- **Rollback Safe**: Delete `/probabilistic` and core engine still works
- **Test Independence**: Probabilistic tests don't run core tests
- **Blame Clear**: Bugs are in probabilistic code, not deterministic

## Important Notes

- **`engine/scoring.py` is version-locked**: Changes here modify the economics and require test updates.
- **State is explicit**: Current inputs are in `engine/state.py`, not in external files.
- **No I/O in scoring**: The math functions are pure and deterministic.
- **Tests are locks**: All test files prevent unintended changes to calculations and contracts.

## Design Principles

1. **Pure functions first** – no side effects
2. **Math is immutable** – the scoring logic never mutates state
3. **State is explicit** – no hidden globals
4. **Readable > clever** – this is decision support, not a Kaggle entry
5. **One responsibility per file**

## Daily AI Assistant (Calibration)

The Daily AI Assistant helps you maintain calibration of the leverage model by accumulating context over time and generating NotebookLM-ready prompts for systematic review.

### What It Does

- **Context Journal**: Append-only file-based storage (`daily_context.json`) of all case updates, emails, court notes, and timeline changes
- **Prompt Generation**: Creates structured calibration prompts for NotebookLM that include:
  - Full accumulated context (all prior entries)
  - Current deterministic engine snapshot
  - Explicit assumptions audit
  - Calibration questionnaire (fact validation, drift detection, pressure level review, settlement corridor sanity check)
  - Required JSON output schema

### How to Use

#### Dashboard (Recommended)

Run the dashboard and scroll to the **Daily AI (Calibration)** panel:

```bash
cd procedural_leverage_engine
streamlit run web/dashboard.py
```

In the panel:
1. Paste new context (emails, notes, updates) in the text area
2. Select entry type (text/email/court_note/phone_call/other)
3. Click **Save to Journal** to append with timestamp
4. Click **Generate NotebookLM Prompt** to build the calibration prompt
5. Copy the generated prompt and paste into NotebookLM
6. Review the LLM's structured JSON output for drift detection and calibration recommendations

#### CLI (Headless)

Add context and generate prompt from command line:

```bash
# Add context and generate prompt
python -m cli.run daily-ai \
  --text "New email from opposing counsel received..." \
  --entry-type email \
  --sv1a 0.6 --sv1b 0.7 --sv1c 0.5 \
  --export-md --print-prompt
```

Options:
- `--text, -t`: New context text (required)
- `--entry-type, -e`: Type of entry (text/email/court_note/phone_call/other)
- `--sv1a/--sv1b/--sv1c`: Current SV values for engine snapshot
- `--limit, -l`: Limit context entries (0 = all)
- `--export-md, -m`: Also export prompt as Markdown file
- `--print-prompt, -p`: Print generated prompt to stdout

### Output Structure

The calibration prompt generates JSON structured output including:

```json
{
  "timestamp_utc": "2024-01-15T10:30:00",
  "model_version": "LEVQUANT_CALIBRATION_TEMPLATE_v1.0",
  "lexicon_used": true,
  "engine_snapshot": { ... },
  "assumptions_audit": {
    "assumptions_light_or_heavy": "light|mixed|heavy",
    "top_5_load_bearing_assumptions": [...]
  },
  "fact_checks": [
    {"id": "F1", "claim": "...", "status": "INFERRED", "probability": 0.7, ...}
  ],
  "drift_detection": {
    "drift_score": 0.3,
    "where_drift_detected": [...],
    "required_corrections": [...]
  },
  "tripwire_calibration": {
    "pressure_level_expected": 7,
    "pressure_level_actual": 6.5,
    "explain_in_plain_english": "..."
  },
  "settlement_corridor_check": {
    "anchor_gbp": 15000000,
    "minimum_objective_gbp": 9000000,
    "corridor_alignment": "aligned",
    "why": "..."
  },
  "insurer_logic": {
    "fastest_scare_fact": "...",
    "reserve_rights_triggers": [...]
  },
  "daily_actions": {
    "what_to_update_in_inputs": [...],
    "what_to_leave_unchanged": [...],
    "what_to_watch_next": [...]
  }
}
```

### Design Principles

- **No vector store**: Simple append-only JSON file, no embeddings or retrieval
- **No external API calls by default**: Generates prompts for manual copy-paste into NotebookLM
- **Court-safe language**: Prompt instructs LLM to use "alleged", "inferred", "supported by evidence" — never absolute claims
- **Deterministic engine consumption**: Uses `cli.run.run_engine()` for engine snapshots, never imports from `/engine` directly
- **Full context**: All journal entries included in prompt (no summarization) for complete audit trail

