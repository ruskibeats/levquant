# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-02-06

### Added
- **Contract Hardening**: Added pyproject.toml for packaging and distribution
- **Schema Validation**: Added schemas/engine_output.json as version-locked JSON contract
- **Validation Script**: Added schemas/validate_schema.py for schema contract validation
- **CI Pipeline**: Added .github/workflows/ci.yml for automated testing and validation
- **CLI Command**: Added `ple` command-line tool via project.scripts
- **Installation**: Added pip install support with development dependencies
- **Probabilistic Extensions**: Added /probabilistic directory with Monte Carlo skeleton
  - Added Beta, Uniform, Normal, Triangular, TruncatedNormal distributions
  - Added monte_carlo_sample() for uncertainty quantification
  - Added 8 predefined stress scenarios
  - Added Pydantic schemas for JSON contracts
  - Added batch_run() for efficient sampling
- **Monte Carlo Demo**: Added run_monte_carlo.py (250,000 sample demonstration)
- **Stress Test**: Added run_10m_stress_test.py (10M sample hostile stress test)

### Changed
- **README**: Added CI badge, installation instructions, packaging documentation
- **Architecture**: Strict separation between deterministic and probabilistic layers
- **Principle**: NEVER import from /engine in probabilistic code

### Security
- **Zero Core Pollution**: Probabilistic code never imports from /engine
- **Rollback Safe**: Delete /probabilistic and core engine still works

## [1.1.0] - 2026-02-06

### Added
- **JSON Output**: Added --json flag to CLI for machine-readable output
- **Schema Models**: Added Pydantic models in probabilistic/schemas.py
- **CLI Tests**: Added test_cli.py for human/JSON mode validation
- **Schema Validation**: Added JSON schema validation tests

### Changed
- **CLI**: Enhanced with --json and --help flags
- **Output**: Structured JSON format for automation and integrations

## [1.0.0] - 2026-02-06

### Added
- **Core Engine**: Deterministic UPLS calculation engine
  - engine/scoring.py - UPLS math (immutable)
  - engine/state.py - current case inputs
  - engine/evaluation.py - decision logic (ACCEPT, COUNTER, REJECT, HOLD)
  - engine/interpretation.py - human-readable labels
- **CLI Interface**: Command-line entry point (cli/run.py)
- **Test Suite**: 74 tests locking all core outputs
  - test_scoring.py - baseline outputs
  - test_evaluation.py - thresholds, confidence, tripwire
  - test_interpretation.py - language, contracts, formatting
  - test_cli.py - human/JSON modes, schema validation
- **Scenarios**: /scenarios directory for sweeps and presets
- **Tripwire**: Cost-based escalation threshold

### Design Principles
- Pure functions first – no side effects
- Math is immutable – scoring logic never mutates state
- State is explicit – no hidden globals
- Readable > clever – decision support, not Kaggle entry
- One responsibility per file

[1.2.0]: https://github.com/ruskibeats/levquant/releases/tag/v1.2.0
[1.1.0]: https://github.com/ruskibeats/levquant/releases/tag/v1.1.0
[1.0.0]: https://github.com/ruskibeats/levquant/releases/tag/v1.0.0