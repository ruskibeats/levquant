"""
Output locks for interpretation layer.

This test locks the human-readable language mappings.
If this test ever fails, the interpretation layer has changed.
"""

import pytest
from engine.interpretation import (
    interpret_upls_range,
    interpret_decision,
    interpret_tripwire,
    interpret_confidence,
    get_full_interpretation,
    format_summary
)


class TestUPLSRangeInterpretation:
    """
    Lock UPLS range interpretation strings.
    
    These tests ensure that the language used to describe leverage positions
    is consistent and posture-based (not outcome-based).
    """
    
    def test_low_leverage_interpretation(self):
        """Test interpretation for low leverage (< 0.30)."""
        assert interpret_upls_range(0.29) == "Low procedural leverage - weak positioning"
        assert interpret_upls_range(0.00) == "Low procedural leverage - weak positioning"
        
    def test_limited_leverage_interpretation(self):
        """Test interpretation for limited leverage (0.30 to 0.50)."""
        assert interpret_upls_range(0.30) == "Limited leverage - defensive posture required"
        assert interpret_upls_range(0.40) == "Limited leverage - defensive posture required"
        assert interpret_upls_range(0.49) == "Limited leverage - defensive posture required"
        
    def test_moderate_leverage_interpretation(self):
        """Test interpretation for moderate leverage (0.50 to 0.70)."""
        assert interpret_upls_range(0.50) == "Moderate leverage - routine dispute parameters"
        assert interpret_upls_range(0.60) == "Moderate leverage - routine dispute parameters"
        assert interpret_upls_range(0.69) == "Moderate leverage - routine dispute parameters"
        
    def test_strong_leverage_interpretation(self):
        """Test interpretation for strong leverage (0.70 to 0.85)."""
        assert interpret_upls_range(0.70) == "Strong leverage - favorable negotiating position"
        assert interpret_upls_range(0.77) == "Strong leverage - favorable negotiating position"
        assert interpret_upls_range(0.84) == "Strong leverage - favorable negotiating position"
        
    def test_very_high_leverage_interpretation(self):
        """Test interpretation for very high leverage (>= 0.85)."""
        assert interpret_upls_range(0.85) == "Very high procedural leverage - upper-bound positioning"
        assert interpret_upls_range(0.90) == "Very high procedural leverage - upper-bound positioning"
        assert interpret_upls_range(1.00) == "Very high procedural leverage - upper-bound positioning"
        
    def test_language_is_posture_based(self):
        """Verify language describes posture, not outcomes."""
        # Should contain posture words, not outcome words
        low = interpret_upls_range(0.10)
        high = interpret_upls_range(0.90)
        
        # Check for posture-based language
        assert "leverage" in low.lower()
        assert "leverage" in high.lower()
        
        # Should NOT contain outcome-based language
        assert "win" not in low.lower()
        assert "win" not in high.lower()
        assert "lose" not in low.lower()
        assert "lose" not in high.lower()


class TestDecisionInterpretation:
    """
    Lock decision interpretation strings.
    
    These tests ensure that decision explanations are descriptive,
    not justificatory (evaluative).
    """
    
    def test_accept_decision(self):
        """Test ACCEPT decision interpretation."""
        result = interpret_decision("ACCEPT")
        expected = "Model indicates acceptance is consistent with current leverage posture."
        assert result == expected
        
    def test_counter_decision(self):
        """Test COUNTER decision interpretation."""
        result = interpret_decision("COUNTER")
        expected = "Model indicates counter-offer is appropriate given current leverage posture."
        assert result == expected
        
    def test_reject_decision(self):
        """Test REJECT decision interpretation."""
        result = interpret_decision("REJECT")
        expected = "Model indicates rejection is consistent with current leverage posture."
        assert result == expected
        
    def test_hold_decision(self):
        """Test HOLD decision interpretation."""
        result = interpret_decision("HOLD")
        expected = "Model indicates maintaining position is appropriate given current leverage posture."
        assert result == expected
        
    def test_unknown_decision(self):
        """Test unknown decision handling."""
        result = interpret_decision("UNKNOWN")
        assert result == "Unknown decision"
        
    def test_language_is_descriptive(self):
        """Verify language is descriptive, not justificatory."""
        accept = interpret_decision("ACCEPT")
        reject = interpret_decision("REJECT")
        
        # Should use "Model indicates" (descriptive)
        assert "Model indicates" in accept
        assert "Model indicates" in reject
        
        # Should NOT use evaluative language like "strong enough", "fundamentally weak"
        assert "strong enough" not in accept
        assert "fundamentally weak" not in reject


class TestTripwireInterpretation:
    """
    Lock tripwire status interpretation strings.
    
    These tests ensure that tripwire language is assessment-based,
    not prediction-based.
    """
    
    def test_safe_zone(self):
        """Test safe zone interpretation."""
        assert interpret_tripwire(4.9) == "Safe zone - no immediate procedural concerns"
        assert interpret_tripwire(0.0) == "Safe zone - no immediate procedural concerns"
        
    def test_caution_zone(self):
        """Test caution zone interpretation."""
        assert interpret_tripwire(5.0) == "Caution zone - monitor for changes"
        assert interpret_tripwire(6.0) == "Caution zone - monitor for changes"
        assert interpret_tripwire(7.4) == "Caution zone - monitor for changes"
        
    def test_critical_zone(self):
        """Test critical zone interpretation."""
        assert interpret_tripwire(7.5) == "Critical zone - tripwire triggered, elevated attention required"
        assert interpret_tripwire(8.0) == "Critical zone - tripwire triggered, elevated attention required"
        assert interpret_tripwire(10.0) == "Critical zone - tripwire triggered, elevated attention required"
        
    def test_language_is_assessment_based(self):
        """Verify language is assessment-based, not prediction-based."""
        critical = interpret_tripwire(8.0)
        
        # Should use "elevated attention" (assessment)
        assert "elevated attention" in critical
        
        # Should NOT use predictive language like "heightened risk"
        assert "heightened risk" not in critical


class TestConfidenceInterpretation:
    """
    Lock confidence level interpretation strings.
    
    These tests ensure that confidence explanations are neutral
    and model-attributed.
    """
    
    def test_very_low_confidence(self):
        """Test Very Low confidence interpretation."""
        result = interpret_confidence("Very Low")
        expected = "Model indicates low confidence in current leverage assessment."
        assert result == expected
        
    def test_low_confidence(self):
        """Test Low confidence interpretation."""
        result = interpret_confidence("Low")
        expected = "Model indicates limited confidence in current leverage assessment."
        assert result == expected
        
    def test_moderate_confidence(self):
        """Test Moderate confidence interpretation."""
        result = interpret_confidence("Moderate")
        expected = "Model indicates moderate confidence in current leverage assessment."
        assert result == expected
        
    def test_good_confidence(self):
        """Test Good confidence interpretation."""
        result = interpret_confidence("Good")
        expected = "Model indicates good confidence in current leverage assessment."
        assert result == expected
        
    def test_strong_confidence(self):
        """Test Strong confidence interpretation."""
        result = interpret_confidence("Strong")
        expected = "Model indicates strong confidence in current leverage assessment."
        assert result == expected
        
    def test_unknown_confidence(self):
        """Test unknown confidence handling."""
        result = interpret_confidence("Unknown")
        assert result == "Unknown confidence level"
        
    def test_language_is_model_attributed(self):
        """Verify confidence language is model-attributed."""
        strong = interpret_confidence("Strong")
        
        # Should use "Model indicates"
        assert "Model indicates" in strong


class TestFullInterpretation:
    """
    Lock the output contract for get_full_interpretation.
    """
    
    def test_full_interpretation_structure(self):
        """Test that full interpretation returns expected structure."""
        result = get_full_interpretation(0.641, 6.41, "HOLD", "Moderate")
        
        # Check all required keys are present
        assert 'leverage_position' in result
        assert 'decision_explanation' in result
        assert 'tripwire_status' in result
        assert 'confidence_explanation' in result
        
    def test_full_interpretation_types(self):
        """Test that full interpretation returns correct types."""
        result = get_full_interpretation(0.641, 6.41, "HOLD", "Moderate")
        
        assert isinstance(result['leverage_position'], str)
        assert isinstance(result['decision_explanation'], str)
        assert isinstance(result['tripwire_status'], str)
        assert isinstance(result['confidence_explanation'], str)
        
    def test_full_interpretation_values(self):
        """Test that full interpretation computes correct values."""
        result = get_full_interpretation(0.641, 6.41, "HOLD", "Moderate")
        
        assert result['leverage_position'] == "Moderate leverage - routine dispute parameters"
        assert result['decision_explanation'] == "Model indicates maintaining position is appropriate given current leverage posture."
        assert result['tripwire_status'] == "Caution zone - monitor for changes"
        assert result['confidence_explanation'] == "Model indicates moderate confidence in current leverage assessment."


class TestFormatSummary:
    """
    Lock the output contract for format_summary.
    
    These tests ensure that the CLI summary format is consistent.
    """
    
    def test_format_summary_structure(self):
        """Test that summary has expected sections."""
        state = {'SV1a': 0.38, 'SV1b': 0.86, 'SV1c': 0.75}
        scores = {'upls': 0.641, 'tripwire': 6.41}
        risk_assessment = {
            'decision': 'HOLD',
            'confidence': 'Moderate',
            'tripwire_triggered': False
        }
        
        summary = format_summary(state, scores, risk_assessment)
        
        # Check for expected sections
        assert "PROCEDURAL LEVERAGE ENGINE - CASE ANALYSIS" in summary
        assert "INPUTS:" in summary
        assert "SCORES:" in summary
        assert "DECISION:" in summary
        assert "INTERPRETATION:" in summary
        
    def test_format_summary_values(self):
        """Test that summary contains correct values."""
        state = {'SV1a': 0.38, 'SV1b': 0.86, 'SV1c': 0.75}
        scores = {'upls': 0.641, 'tripwire': 6.41}
        risk_assessment = {
            'decision': 'HOLD',
            'confidence': 'Moderate',
            'tripwire_triggered': False
        }
        
        summary = format_summary(state, scores, risk_assessment)
        
        # Check for expected values
        assert "0.38" in summary  # SV1a
        assert "0.86" in summary  # SV1b
        assert "0.75" in summary  # SV1c
        assert "0.641" in summary  # UPLS
        assert "6.41" in summary  # Tripwire
        assert "HOLD" in summary  # Decision
        assert "Moderate" in summary  # Confidence
        assert "No" in summary  # Tripwire triggered
        
    def test_format_summary_with_missing_data(self):
        """Test that summary handles missing data gracefully."""
        state = {}  # Missing all keys
        scores = {}  # Missing all keys
        risk_assessment = {}  # Missing all keys
        
        summary = format_summary(state, scores, risk_assessment)
        
        # Should use 'N/A' for missing values
        assert "N/A" in summary
        # Should not crash
        assert summary is not None
        
    def test_format_summary_safe_formatting(self):
        """Test that summary formatting is type-safe."""
        state = {'SV1a': 'invalid', 'SV1b': 0.86, 'SV1c': 0.75}
        scores = {'upls': 0.641, 'tripwire': 6.41}
        risk_assessment = {
            'decision': 'HOLD',
            'confidence': 'Moderate',
            'tripwire_triggered': False
        }
        
        summary = format_summary(state, scores, risk_assessment)
        
        # Should handle non-numeric values gracefully
        assert summary is not None
        assert "N/A" in summary  # For invalid SV1a