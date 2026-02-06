# Architecture

## Engine Philosophy

The Procedural Leverage Engine is a **deterministic decision-support system** designed for commercial dispute settlement analysis. It prioritizes auditability, reproducibility, and clear separation of concerns over complexity or "clever" optimizations.

## Core Principles

1. **Deterministic Core**: All scoring functions produce identical outputs for identical inputs. No randomness, no probabilistic elements, no hidden state.

2. **Explicit Boundaries**: Clear separation between:
   - **Scoring layer** (`engine/scoring.py`): Pure mathematical functions
   - **Evaluation layer** (`engine/evaluation.py`): Business logic and thresholds
   - **Interpretation layer** (`engine/interpretation.py`): Human-readable output

3. **Immutable Math**: The scoring logic in `engine/scoring.py` is version-locked. Changes require explicit test updates and version bumping.

4. **No External Dependencies**: Pure Python implementation ensures:
   - Long-term stability under refactor
   - Environment independence
   - Auditability by non-technical stakeholders

## Module Boundaries

### `/engine` - Core Logic (Invariant)

- **`scoring.py`**: UPLS and tripwire calculations (pure functions, no side effects)
- **`state.py`**: Current case state (explicit inputs, no hidden globals)
- **`evaluation.py`**: Decision thresholds and business logic (never recomputes UPLS)
- **`interpretation.py`**: Human-readable labels and summaries (language layer only)

**Rule**: `/engine` modules never import from `/scenarios` or external sources.

### `/scenarios` - Hypothetical States (Optional)

- **`sweeps.py`**: Parameter sweeps and what-if analysis
- **`presets.py`**: Named scenario presets

**Rule**: `/scenarios` modules can import from `/engine` but never vice versa.

### `/cli` - Interface (Thin)

- **`run.py`**: Command-line entry point (load → compute → print → exit)

**Rule**: No loops, menus, or interactivity. Single execution path.

### `/tests` - Output Locks (Non-Negotiable)

- **`test_scoring.py`**: Locks baseline scoring outputs

**Rule**: If tests fail, stop and investigate. Economics have changed.

## Explicit Boundary: Probabilistic Extensions

**Probabilistic modules must live outside `/engine`**.

Future extensions (e.g., Monte Carlo simulations, Bayesian updates) should be organized as:
- `/probabilistic/` - Separate module with its own test suite
- Clearly marked as "experimental" or "supplemental"
- Never modify the deterministic core in `/engine/scoring.py`

This separation ensures:
- Deterministic baseline remains auditable
- Probabilistic extensions can evolve independently
- Clear distinction between fact (deterministic) and judgment (probabilistic)

## UPLS Clarification

**UPLS is NOT**:
- A probability of success
- A monetary valuation
- Legal advice
- A substitute for forensic analysis

**UPLS IS**:
- A scalar [0.0, 1.0] representing weighted procedural leverage
- A decision-support metric for settlement pressure assessment
- A deterministic aggregation of three independent vectors
- A tool for disciplined, structured analysis

## Version Discipline

- v1.x: Deterministic engine (current release)
- v2.x: Probabilistic extensions (separate module)
- Breaking changes to `scoring.py` require major version bump

## Future-Proofing

The architecture is designed to:
- Support probabilistic extensions without breaking the deterministic core
- Allow alternative weightings via scenario sweeps
- Enable external state ingestion (YAML, JSON, database) without touching math
- Maintain auditability as complexity grows

**Golden Rule**: If a change requires modifying `engine/scoring.py`, ask:
1. Is this necessary?
2. Have tests been updated?
3. Has the version been bumped?
4. Is this documented in CHANGELOG.md?