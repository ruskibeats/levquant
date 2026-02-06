# Changelog

All notable changes to the Procedural Leverage Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-02

### Added
- Initial release of deterministic Procedural Leverage Engine
- Core UPLS calculation with weighted aggregation (40/35/25 weighting)
- Tripwire scoring for threshold assessment
- Explicit state management in `engine/state.py`
- Decision evaluation logic (ACCEPT, COUNTER, REJECT, HOLD)
- Human-readable interpretation layer
- Scenario sweep capabilities for what-if analysis
- Preset scenario library
- Command-line interface (`python -m cli.run`)
- Comprehensive test suite with output locks
- Professional documentation with defensive framing

### Architecture
- Deterministic scoring layer (pure functions, no side effects)
- Separated evaluation layer (thresholded, categorical decisions)
- Immutable math core in `engine/scoring.py`
- No external dependencies (pure Python)

### Design Principles
- Pure functions first
- Math is immutable
- State is explicit
- Readable > clever
- One responsibility per file

### Documentation
- Comprehensive README with assumptions and non-goals
- Inline docstrings for all functions
- Project structure aligned with codebase

### Testing
- 7 test cases covering baseline, edge cases, and validation
- Output locks prevent unintended scoring changes
- All tests passing on initial release