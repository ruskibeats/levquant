"""Tests for probabilistic/bayesian.py - Truth Decay model."""

from __future__ import annotations

import pytest

from probabilistic.bayesian import (
    EvidenceDecay,
    DecayAssumptions,
    quick_decay_check,
)


class TestEvidenceDecay:
    """Tests for EvidenceDecay model."""

    def test_no_decay_at_zero_days(self) -> None:
        """Test that posterior equals prior at day 0."""
        model = EvidenceDecay()
        posterior = model.calculate_posterior(0.7, 0.02, 0)
        assert posterior == 0.7

    def test_decay_increases_with_days(self) -> None:
        """Test that posterior decreases monotonically with days."""
        model = EvidenceDecay()
        p_30 = model.calculate_posterior(0.7, 0.02, 30)
        p_60 = model.calculate_posterior(0.7, 0.02, 60)
        p_90 = model.calculate_posterior(0.7, 0.02, 90)
        
        assert p_30 > p_60 > p_90

    def test_posterior_bounded(self) -> None:
        """Test that posterior is bounded between 1% and 99%."""
        model = EvidenceDecay()
        # High decay over long time
        posterior = model.calculate_posterior(0.99, 0.1, 1000)
        assert 0.01 <= posterior <= 0.99

    def test_inference_labels_returned(self) -> None:
        """Test that inference labels are court-safe."""
        model = EvidenceDecay()
        label = model.get_inference_label(0.15)
        
        assert "likelihood" in label.lower()
        assert "doubt" not in label.lower()  # Avoid legal standard terms
        assert "proof" not in label.lower()

    def test_run_decay_analysis_structure(self) -> None:
        """Test decay analysis returns expected structure."""
        model = EvidenceDecay()
        result = model.run_decay_analysis(60, 0.6, 0.02)
        
        assert "timestamp_utc" in result
        assert "audit_hash" in result
        assert "model_version" in result
        assert "assumptions" in result
        assert "results" in result
        assert "projections" in result
        assert "disclaimer" in result
        assert "court_safe_summary" in result

    def test_assumptions_in_output(self) -> None:
        """Test that assumptions are echoed in output."""
        model = EvidenceDecay()
        result = model.run_decay_analysis(45, 0.5, 0.03)
        
        assert result["assumptions"]["prior_probability"] == 0.5
        assert result["assumptions"]["decay_rate_per_day"] == 0.03
        assert result["assumptions"]["days_since_reference"] == 45

    def test_time_to_threshold_calculated(self) -> None:
        """Test time to threshold calculations."""
        model = EvidenceDecay()
        days = model._calculate_time_to_threshold(0.8, 0.02, 0.5)
        
        assert days is not None
        assert days > 0

    def test_court_safe_summary_contains_disclaimer(self) -> None:
        """Test summary contains appropriate caveats."""
        model = EvidenceDecay()
        result = model.run_decay_analysis(120, 0.6, 0.02)
        summary = result["court_safe_summary"]
        
        assert "inference" in summary.lower()
        assert "not evidence" in summary.lower()

    def test_disclaimer_present(self) -> None:
        """Test disclaimer is present in output."""
        model = EvidenceDecay()
        result = model.run_decay_analysis(30)
        
        assert "time-based inference model" in result["disclaimer"]
        assert "not proof" in result["disclaimer"]


class TestQuickDecayCheck:
    """Tests for quick_decay_check function."""

    def test_quick_check_returns_results(self) -> None:
        """Test quick check returns minimal results."""
        result = quick_decay_check(100, 0.5, 0.02)
        
        assert "results" in result
        assert "posterior_probability" in result["results"]

    def test_quick_check_uses_defaults(self) -> None:
        """Test quick check with defaults."""
        result = quick_decay_check(60)
        
        # Should use default prior=0.5, decay=0.02
        assert result["assumptions"]["prior_probability"] == 0.5
        assert result["assumptions"]["decay_rate_per_day"] == 0.02
