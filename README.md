# Procedural Leverage Engine (LEVQUANT)

[![CI](https://github.com/ruskibeats/levquant/workflows/CI/badge.svg)](https://github.com/ruskibeats/levquant/actions)

**Deterministic decision-support framework for commercial dispute settlement negotiations.**

This project computes a Unified Procedural Leverage Score (UPLS) and provides comprehensive risk analytics for settlement strategy. It is designed as a decision aid—not a decision-maker—and uses only court-safe, auditable language throughout.

---

## Quick Start

```bash
# Install
cd procedural_leverage_engine
pip install -e .

# Run CLI
ple --help

# Run Dashboard
streamlit run web/dashboard.py
```

---

## What This System Does

LEVQUANT provides **deterministic, auditable decision support** for settlement negotiations through four integrated layers:

### 1. Core Engine (Deterministic Scoring)
- **UPLS**: Unified Procedural Leverage Score [0.0, 1.0]
- **Three Input Vectors**:
  - SV1a: Claim validity strength
  - SV1b: Procedural advantage
  - SV1c: Cost asymmetry
- **Decision Outputs**: ACCEPT, COUNTER, HOLD, REJECT

### 2. Settlement Bands (Event-Driven Pricing)
- **BASE**: £2.5m–£4m (0 flags) — Present-day, evidence-only value
- **VALIDATION**: £5m–£9m (1 validation flag) — After external validation event
- **TAIL**: £12m–£15m (≥2 tail flags) — Existential containment pricing

### 3. Forensic Deep Dive (Risk Indicators)
- **Truth Decay**: Time-based evidence strength inference
- **GDPR Forensics**: Data integrity/iniquity risk indicators
- **Insurance Shadow Reserve**: Locked capital estimation

### 4. Daily AI Assistant (Calibration)
- Context journal with UTC timestamps
- NotebookLM-ready prompt generation
- Drift detection and fact validation

---

## Architecture

```
procedural_leverage_engine/
├── engine/                    # Core deterministic scoring (immutable)
│   ├── scoring.py            # UPLS math
│   ├── evaluation.py         # Decision logic
│   └── interpretation.py     # Human-readable labels
│
├── decision_support/          # Risk analytics (outside engine)
│   ├── settlement_bands.py   # Three-band settlement framework
│   ├── insurance_reserve.py  # Reserve pressure analysis
│   ├── gdpr_liability.py     # GDPR exposure quantification
│   ├── gdpr_forensics.py     # Data integrity risk indicators
│   └── insurance_shadow.py   # Shadow reserve/dead money
│
├── probabilistic/             # Inference models (outside engine)
│   └── bayesian.py           # Truth decay model
│
├── ai_assistant/              # Daily calibration
│   ├── context_journal.py    # Append-only context storage
│   └── daily_calibration.py  # Prompt generation
│
├── web/                       # Streamlit dashboard
│   └── dashboard.py
│
├── cli/                       # Command-line interface
│   └── run.py
│
└── tests/                     # Comprehensive test suite
```

**Critical Constraint**: No code in `decision_support/`, `probabilistic/`, or `ai_assistant/` imports from `engine/` directly. All engine access via `cli.run.run_engine()`.

---

## Installation

### From Source

```bash
cd procedural_leverage_engine
pip install -e .
```

This installs the `ple` command-line tool:

```bash
ple --help                    # Show usage
ple --json                    # JSON output
ple calibrate                 # Run calibration probe
ple daily-ai --text "..."     # Add to context journal
```

### Development Installation

```bash
pip install -e ".[dev]"
```

Includes pytest, black, and ruff.

---

## Usage

### Command Line

#### Basic Execution

```bash
python -m cli.run
```

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

#### JSON Output

```bash
python -m cli.run --json
```

#### Calibration Probe

```bash
python -m cli.run calibrate
```

Runs independent LLM calibration assessment.

#### Daily AI Context

```bash
python -m cli.run daily-ai \
  --text "New email from opposing counsel..." \
  --entry-type email \
  --sv1a 0.6 --sv1b 0.7 --sv1c 0.5
```

---

## Dashboard

### Run the Dashboard

```bash
streamlit run web/dashboard.py
```

### Dashboard Panels

1. **Settlement Bands**: Visual band selector with flag-driven activation
2. **Monetary Corridor**: Event-driven repricing with visual feedback
3. **Daily AI (Calibration)**: Context journal and NotebookLM prompts
4. **Forensic Deep Dive** (Advanced): Truth decay, GDPR forensics, shadow reserve
5. **Export**: JSON, PDF, and calibration outputs

---

## Settlement Bands Framework

### Band Definitions

| Band | Range | Flags Required | Description |
|------|-------|----------------|-------------|
| **BASE** | £2.5m–£4m | 0 | Present-day, evidence-only value |
| **VALIDATION** | £5m–£9m | 1 validation flag | After external validation event |
| **TAIL** | £12m–£15m | ≥2 tail flags | Existential containment pricing |

### Validation Flags (1 required for VALIDATION band)
- `judicial_comment_on_record`
- `sra_investigation_open`
- `insurer_expanded_reservation`
- `court_directed_explanation`

### Tail Flags (2 required for TAIL band)
- `adverse_judicial_language`
- `sra_formal_action`
- `insurance_coverage_stress`
- `part_26a_disclosure_conflict`
- `criminal_investigation_escalation`

### Usage

```python
from decision_support.settlement_bands import SettlementBandCalculator

calc = SettlementBandCalculator(active_flags=["judicial_comment_on_record"])
summary = calc.generate_band_summary()

print(summary["current_band"])        # "VALIDATION"
print(summary["current_range"])       # "£5.0m–£9.0m"
print(summary["what_moves_up"])       # Next band requirements
```

---

## Forensic Deep Dive Modules

### 1. Truth Decay (probabilistic/bayesian.py)

Time-based inference model for evidence strength assessment.

```python
from probabilistic.bayesian import quick_decay_check

result = quick_decay_check(
    days_since_event=240,
    prior=0.6,
    decay_rate=0.02
)

print(result["results"]["posterior_probability"])  # 0.289
print(result["results"]["inference_strength"])     # "Low likelihood - improbable"
```

**Key Features**:
- Exponential decay: P(t) = P(0) × exp(-λt)
- Court-safe labels ("likelihood", not "proof")
- Audit hash and explicit assumptions
- Disclaimer: "time-based inference model, not proof of non-existence"

### 2. GDPR Forensics (decision_support/gdpr_forensics.py)

Data integrity risk assessment with court-safe language.

```python
from decision_support.gdpr_forensics import quick_integrity_check

result = quick_integrity_check(
    sar_gap_proven=True,
    manual_override_proven=True
)

print(result["integrity_risk"]["risk_score"])      # 60
print(result["integrity_risk"]["risk_level"])      # "HIGH"
print(result["ico_reportable"])                    # True
print(result["insurer_impact"]["iniquity_exclusion"])  # "Risk elevated"
```

**Risk Scoring**:
- SAR gap proven: 25 points
- Manual override proven: 35 points
- Special category involved: 20 points
- Shadow data discovered: 15 points
- Systemic pattern: 15 points

**Court-Safe Language**:
- "Potential DPA 2018 s.173 exposure indicator" (not "fraud proven")
- "ICO likely reportable" (not "must report")
- "Iniquity exclusion risk elevated" (not "policy void")

### 3. Insurance Shadow Reserve (decision_support/insurance_shadow.py)

Illustrative reserve and dead money cost estimation.

```python
from decision_support.insurance_shadow import quick_shadow_check

result = quick_shadow_check(
    claim_value_gbp=5_000_000,
    litigation_stage="procedural_irregularity_flagged"
)

print(result["shadow_reserve"]["estimated_reserve_locked_gbp"])  # 1,750,000
print(result["dead_money_cost"]["annual_cost_gbp"])              # 105,000
print(result["negotiation_lever"]["lever_strength"])             # "HIGH"
```

**Stage-Based Ratios**:
- Notification: 5%
- Defence filed: 15%
- Procedural irregularity flagged: 35%
- Trial listed: 65%

**Disclaimer**: "Illustrative reserve ratios for negotiation analysis. Not actual insurer-specific reserves."

---

## Insurance Reserve Model

Reserve pressure analysis for negotiation leverage.

```python
from decision_support.insurance_reserve import InsuranceReserveModel

model = InsuranceReserveModel(case_reserve_gbp=2_000_000)
report = model.generate_reserve_report(
    settlement_demand_gbp=5_000_000,
    active_flags=["sra_formal_action"]
)

print(report["gap_analysis"]["reserve_gap"])           # 2,250,000
print(report["coverage_stress"]["stress_level"])       # "ELEVATED"
print(report["negotiation_leverage"]["score"])         # 5.25
```

---

## GDPR Liability Module

Quantified GDPR exposure for Hiloka and Maven.

```python
from decision_support.gdpr_liability import HILOKA_GDPR_EXPOSURE

report = HILOKA_GDPR_EXPOSURE.generate_total_exposure_report()

print(report["article_82_exposure"]["total_exposure_high"])  # 375,000
print(report["ico_fine_exposure"]["max_fine_calculated"])   # 200,000
print(report["combined_maximum_exposure"])                  # 575,000
```

---

## Daily AI Assistant

### Context Journal

Append-only file-based storage (`daily_context.json`):

```python
from ai_assistant.context_journal import add_context, get_all_context

# Add entry
add_context(
    doc_text="New email from Freeths received...",
    entry_type="email",
    source="dashboard"
)

# Retrieve all context
context = get_all_context(limit=50)
```

### Calibration Prompt Generation

```python
from ai_assistant.daily_calibration import DailyAICalibrator

calibrator = DailyAICalibrator()
prompt = calibrator.build_prompt(
    all_context=context,
    new_context="New judicial comment received...",
    engine_snapshot=engine_output,
    assumptions_snapshot=assumptions
)
```

**Prompt Includes**:
- Engine snapshot (UPLS, tripwire, decision)
- Settlement band summary
- Forensic deep dive outputs
- Explicit assumptions
- Calibration questionnaire
- Required JSON output schema

---

## Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Test Coverage

| Module | Tests |
|--------|-------|
| Core engine | 74 |
| Settlement bands | 33 |
| Insurance reserve | 14 |
| GDPR liability | 14 |
| Bayesian decay | 12 |
| GDPR forensics | 12 |
| Insurance shadow | 10 |
| AI assistant | 33 |
| Daily calibration | 23 |
| Calibration probe | 21 |
| **TOTAL** | **233** |

### Critical Test Constraints

```python
# Settlement bands
test_fifteen_million_only_in_tail      # £15m appears ONLY in TAIL
test_base_does_not_exceed_four_million  # BASE capped at £4m
test_validation_does_not_exceed_nine    # VALIDATION capped at £9m

# Bayesian decay
test_decay_increases_with_days          # Monotonic decay
test_posterior_bounded                  # 1%-99% bounds

# GDPR forensics
test_score_changes_with_toggles         # UI visibly changes
```

---

## Court-Safe Language

This system uses only court-safe, non-advocacy language:

| Instead of... | Use... |
|---------------|--------|
| "Fraud proven" | "Potential exposure indicator" |
| "Policy void" | "Iniquity exclusion risk elevated" |
| "Guaranteed outcome" | "Likelihood assessment" |
| "Beyond reasonable doubt" | "High probability inference" |
| "Must report to ICO" | "Likely reportable to ICO" |
| "Actual insurer reserve" | "Illustrative reserve ratio" |

All outputs include explicit disclaimers and audit trails.

---

## Design Principles

1. **Deterministic**: Same inputs → same outputs
2. **Immutable Engine**: `/engine` never changes
3. **No Direct Imports**: Decision support consumes engine via CLI
4. **Court-Safe**: No absolute claims or advocacy language
5. **Auditable**: All outputs include assumptions, timestamps, and hashes
6. **Explicit Assumptions**: All models declare their assumptions
7. **Test Coverage**: Comprehensive test suite prevents regressions

---

## Non-Goals

This system does NOT:
- Predict judicial outcomes
- Provide legal advice
- Replace forensic analysis
- Model opponent psychology
- Make decisions (it's decision **support**)

---

## License

MIT License - See LICENSE file for details.

---

## Disclaimer

**This is decision support software, not legal advice.**

All monetary outputs are **decision-support assumptions**, not legal valuation facts. The system provides analytical frameworks for negotiation strategy—it does not guarantee outcomes or replace professional legal counsel.

**Not Legal Advice**: This software is for informational and analytical purposes only. It does not constitute legal advice and should not be relied upon as a substitute for consultation with qualified legal counsel.

**No Warranty**: The software is provided "as is" without warranty of any kind, express or implied.

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/ruskibeats/levquant/issues
- Documentation: This README and ARCHITECTURE.md
