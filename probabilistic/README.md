# Probabilistic Extensions

**Status**: v2.0-skeleton (planned, not implemented)

## Purpose

This module provides probabilistic extensions on top of the deterministic core engine. It does not modify or replace the core engine—it consumes it via JSON output or the `run_engine()` function.

## Architecture Principle (Critical)

**NEVER IMPORT `/engine` DIRECTLY**

All probabilistic code must:
- Consume CLI JSON output or call `run_engine()`
- Never import `scoring.py`, `evaluation.py`, or `interpretation.py`
- Treat the deterministic engine as a black-box dependency
- Be independently testable and deleteable

This preserves:
- Determinism in `/engine` (sacred)
- Test locks for core engine
- Rollback safety (delete `/probabilistic` without affecting core)
- Clear blame boundaries (bugs are probabilistic, not deterministic)

## Why This Matters

The deterministic engine provides:
- **Leverage posture** (single point estimate)
- **Decision recommendation** (based on fixed thresholds)

The probabilistic layer provides:
- **Uncertainty quantification** (Monte Carlo distributions)
- **Scenario exploration** (stress testing, what-if analysis)
- **Posterior updates** (Bayesian learning from outcomes)

These are **orthogonal concerns**. Mixing them in one module violates separation of concerns and makes testing impossible.

## Directory Structure

```
probabilistic/
├── README.md                 # This file
├── schemas.py                # Pydantic models for JSON contracts
├── __init__.py
├── adapters.py               # CLI subprocess wrapper
├── monte_carlo.py            # SV sampling + aggregation
├── scenarios.py              # Named stress tests
└── tests/
    ├── test_monte_carlo.py   # Distribution checks
    └── test_scenarios.py     # Preset validation
```

## Component Responsibilities

### schemas.py
- Pydantic models for CLI JSON schema validation
- Input/output contracts
- Type safety for probabilistic processing

### adapters.py
- Wrapper around `python -m cli.run --json`
- Subprocess management
- Error handling and retry logic
- Returns structured Python objects (not JSON strings)

### monte_carlo.py
- Distribution models (Beta, Normal, Triangular)
- SV sampling algorithms
- Decision aggregation (how often does ACCEPT appear?)
- Tripwire distribution analysis

### scenarios.py
- Named stress scenarios:
  - "cost_spike": SV1c = 1.0 (maximum cost asymmetry)
  - "judge_hostile": Adjust evaluation thresholds
  - "invalidity_collapse": SV1a = 0.1 (minimum claim validity)
- Batch scenario execution
- Result aggregation

## Usage Examples

### Monte Carlo Sampling

```bash
# Sample 10,000 scenarios
python -m probabilistic.monte_carlo --n-samples 10000
```

Output:
```json
{
  "meta": {"n_samples": 10000, "method": "monte_carlo"},
  "distributions": {
    "sv1a_mean": 0.38,
    "sv1a_std": 0.05,
    "sv1b_mean": 0.86,
    "sv1b_std": 0.03,
    "sv1c_mean": 0.75,
    "sv1c_std": 0.08
  },
  "decision_frequencies": {
    "ACCEPT": 1234,
    "COUNTER": 4567,
    "HOLD": 3456,
    "REJECT": 743
  }
}
```

### Stress Scenarios

```bash
# Run named stress tests
python -m probabilistic.scenarios --scenario cost_spike
```

## Non-Goals

This module does not:
- Replace the deterministic engine
- Modify `/engine` in any way
- Predict judicial outcomes (liability, quantum)
- Model opponent psychology or negotiation tactics
- Provide probability-of-success estimates

It exists solely to:
- Quantify uncertainty around deterministic leverage estimates
- Explore scenario space systematically
- Provide structured output for higher-order decision systems

## Design Principles

1. **Never touch `/engine`** – consume via JSON only
2. **Deletable** – can be removed without affecting core
3. **Independently testable** – tests don't depend on core
4. **Explicit contracts** – Pydantic models for all I/O
5. **Separate concerns** – distributions, sampling, adapters are independent

## Integration Pattern

```python
from probabilistic.adapters import run_deterministic_engine

# Get deterministic output as Python dict
result = run_deterministic_engine()

# Access components
upls = result['scores']['upls']
decision = result['evaluation']['decision']

# Never do: from engine.scoring import calculate_comprehensive_score
# That's forbidden.
```

## Safety Guarantees

- **Zero Core Pollution**: No imports from `/engine`
- **Rollback Safe**: Delete `/probabilistic` and core still works
- **Test Independence**: Probabilistic tests don't run core tests
- **Blame Clear**: Bugs are in probabilistic code, not deterministic

## Future Extensions (Out of Scope for v2.0-skeleton)

- Bayesian posterior updating (optional, complex)
- MCMC sampling methods (Metropolis-Hastings)
- Scenario optimization (grid search, genetic algorithms)
- Visualization and reporting
- Database integration for scenario storage

## Version Philosophy

**v2.0-skeleton**: Structure and contracts only  
**v2.1-monte-carlo**: Sampling implementation  
**v2.2-bayesian**: Posterior updating (optional)

Each version adds capability without breaking previous contracts.