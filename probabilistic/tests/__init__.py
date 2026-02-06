"""
Tests for probabilistic extensions.

This test module tests Monte Carlo sampling, scenarios, and adapters
without importing from /engine directly.

Critical Design Principle:
    All tests must use probabilistic.adapters.run_deterministic_engine().
    Never import from /engine directly.
"""

__version__ = "2.0-skeleton"