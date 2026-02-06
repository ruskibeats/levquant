"""
Output locks for evaluation logic.

This test locks the decision thresholds and confidence mappings.
If this test ever fails, the business logic has changed.
"""

import pytest
from engine.evaluation import (
    evaluate_leverage,
    get_decision_confidence,
    is_tripwire_triggered,
    get_risk_assessment,
    Decision,
    THRESHOLDS
)


class TestDecisionThresholds:
    """
    Lock decision threshold boundaries.
    
    These tests ensure that the evaluation logic produces deterministic results.
    If any of these fail, the business logic has changed.
    """
    
    def test_reject_boundary(self):
        """Test REJECT decision at and below critical_low threshold."""
        # Just below critical_low (0.30)
        assert evaluate_leverage(0.29, 2.9) == Decision.REJECT
        # At critical_low
        assert evaluate_leverage(0.30, 3.0) == Decision.COUNTER
        
    def test_counter_boundary(self):
        """Test COUNTER decision between critical_low and marginal."""
        # Just above critical_low
        assert evaluate_leverage(0.31, 3.1) == Decision.COUNTER
        # Just below marginal (0.50)
        assert evaluate_leverage(0.49, 4.9) == Decision.COUNTER
        # At marginal
        assert evaluate_leverage(0.50, 5.0) == Decision.HOLD
        
    def test_hold_boundary_lower(self):
        """Test HOLD decision between marginal and acceptable."""
        # Just above marginal
        assert evaluate_leverage(0.51, 5.1) == Decision.HOLD
        # Just below acceptable (0.70)
        assert evaluate_leverage(0.69, 6.9) == Decision.HOLD
        # At acceptable
        assert evaluate_leverage(0.70, 7.0) == Decision.HOLD
        
    def test_hold_boundary_upper(self):
        """Test HOLD decision in acceptable but not strong range."""
        # Middle of acceptable range
        assert evaluate_leverage(0.77, 7.7) == Decision.HOLD
        # Just below strong (0.85)
        assert evaluate_leverage(0.84, 8.4) == Decision.HOLD
        # At strong
        assert evaluate_leverage(0.85, 8.5) == Decision.ACCEPT
        
    def test_accept_boundary(self):
        """Test ACCEPT decision at and above strong threshold."""
        # Just above strong
        assert evaluate_leverage(0.86, 8.6) == Decision.ACCEPT
        # Maximum value
        assert evaluate_leverage(1.00, 10.0) == Decision.ACCEPT
        
    def test_monotonic_progression(self):
        """Test that decisions progress monotonically with UPLS."""
        test_points = [0.10, 0.35, 0.60, 0.75, 0.90]
        decisions = [
            evaluate_leverage(upls, upls * 10) for upls in test_points
        ]
        
        # Should progress REJECT -> COUNTER -> HOLD -> HOLD -> ACCEPT
        expected = [Decision.REJECT, Decision.COUNTER, Decision.HOLD, Decision.HOLD, Decision.ACCEPT]
        assert decisions == expected
        
    def test_invalid_upls_input(self):
        """Test that invalid UPLS raises ValueError."""
        with pytest.raises(ValueError, match="must be in"):
            evaluate_leverage(-0.1, 5.0)
        
        with pytest.raises(ValueError, match="must be in"):
            evaluate_leverage(1.5, 5.0)
            
    def test_invalid_tripwire_input(self):
        """Test that invalid tripwire raises ValueError."""
        with pytest.raises(ValueError, match="must be in"):
            evaluate_leverage(0.5, -1.0)
        
        with pytest.raises(ValueError, match="must be in"):
            evaluate_leverage(0.5, 15.0)


class TestConfidenceMapping:
    """
    Lock confidence level mappings.
    
    These tests ensure that confidence thresholds are consistent with decision thresholds.
    """
    
    def test_very_low_confidence(self):
        """Test Very Low confidence below 0.30."""
        assert get_decision_confidence(0.29) == "Very Low"
        assert get_decision_confidence(0.00) == "Very Low"
        
    def test_low_confidence(self):
        """Test Low confidence between 0.30 and 0.50."""
        assert get_decision_confidence(0.30) == "Low"
        assert get_decision_confidence(0.40) == "Low"
        assert get_decision_confidence(0.49) == "Low"
        
    def test_moderate_confidence(self):
        """Test Moderate confidence between 0.50 and 0.70."""
        assert get_decision_confidence(0.50) == "Moderate"
        assert get_decision_confidence(0.60) == "Moderate"
        assert get_decision_confidence(0.69) == "Moderate"
        
    def test_good_confidence(self):
        """Test Good confidence between 0.70 and 0.85."""
        assert get_decision_confidence(0.70) == "Good"
        assert get_decision_confidence(0.77) == "Good"
        assert get_decision_confidence(0.84) == "Good"
        
    def test_strong_confidence(self):
        """Test Strong confidence at and above 0.85."""
        assert get_decision_confidence(0.85) == "Strong"
        assert get_decision_confidence(1.00) == "Strong"
        
    def test_invalid_confidence_input(self):
        """Test that invalid UPLS raises ValueError."""
        with pytest.raises(ValueError, match="must be in"):
            get_decision_confidence(-0.1)
        
        with pytest.raises(ValueError, match="must be in"):
            get_decision_confidence(1.5)
            
    def test_confidence_monotonic(self):
        """Test that confidence increases monotonically with UPLS."""
        test_points = [0.10, 0.40, 0.60, 0.80, 0.90]
        confidences = [get_decision_confidence(upls) for upls in test_points]
        
        expected = ["Very Low", "Low", "Moderate", "Good", "Strong"]
        assert confidences == expected


class TestTripwireLogic:
    """
    Lock tripwire trigger logic.
    """
    
    def test_tripwire_not_triggered_below_threshold(self):
        """Test that tripwire is not triggered below default threshold."""
        assert not is_tripwire_triggered(7.4)
        assert not is_tripwire_triggered(0.0)
        assert not is_tripwire_triggered(5.0)
        
    def test_tripwire_triggered_at_threshold(self):
        """Test that tripwire is triggered at default threshold."""
        assert is_tripwire_triggered(7.5)
        
    def test_tripwire_triggered_above_threshold(self):
        """Test that tripwire is triggered above default threshold."""
        assert is_tripwire_triggered(8.0)
        assert is_tripwire_triggered(10.0)
        
    def test_custom_tripwire_threshold(self):
        """Test that custom tripwire threshold works."""
        assert is_tripwire_triggered(9.9, threshold=10.0) == False
        assert is_tripwire_triggered(10.0, threshold=10.0) == True
        assert is_tripwire_triggered(10.1, threshold=10.0) == True


class TestRiskAssessmentContract:
    """
    Lock the output contract for get_risk_assessment.
    
    This test ensures that the function returns the expected structure
    for downstream consumption (CLI, JSON export, etc.).
    """
    
    def test_risk_assessment_structure(self):
        """Test that risk assessment returns expected structure."""
        result = get_risk_assessment(0.641, 6.41)
        
        # Check all required keys are present
        assert 'decision' in result
        assert 'confidence' in result
        assert 'tripwire_triggered' in result
        assert 'upls_value' in result
        assert 'tripwire_value' in result
        
    def test_risk_assessment_types(self):
        """Test that risk assessment returns correct types."""
        result = get_risk_assessment(0.641, 6.41)
        
        assert isinstance(result['decision'], str)
        assert isinstance(result['confidence'], str)
        assert isinstance(result['tripwire_triggered'], bool)
        assert isinstance(result['upls_value'], float)
        assert isinstance(result['tripwire_value'], float)
        
    def test_risk_assessment_values(self):
        """Test that risk assessment computes correct values."""
        result = get_risk_assessment(0.641, 6.41)
        
        assert result['decision'] in ["ACCEPT", "COUNTER", "REJECT", "HOLD"]
        assert result['confidence'] in ["Very Low", "Low", "Moderate", "Good", "Strong"]
        assert result['upls_value'] == 0.641
        assert result['tripwire_value'] == 6.41
        assert result['tripwire_triggered'] == False  # 6.41 < 7.5
        
    def test_risk_assessment_with_high_tripwire(self):
        """Test risk assessment with triggered tripwire."""
        result = get_risk_assessment(0.90, 9.0)
        
        assert result['decision'] == "ACCEPT"
        assert result['confidence'] == "Strong"
        assert result['tripwire_triggered'] == True  # 9.0 >= 7.5
        
    def test_risk_assessment_with_low_tripwire(self):
        """Test risk assessment with low leverage."""
        result = get_risk_assessment(0.25, 2.5)
        
        assert result['decision'] == "REJECT"
        assert result['confidence'] == "Very Low"
        assert result['tripwire_triggered'] == False


class TestThresholdConstants:
    """
    Lock threshold constant values.
    """
    
    def test_threshold_values(self):
        """Test that threshold constants have expected values."""
        assert THRESHOLDS['upls_critical_low'] == 0.30
        assert THRESHOLDS['upls_marginal'] == 0.50
        assert THRESHOLDS['upls_acceptable'] == 0.70
        assert THRESHOLDS['upls_strong'] == 0.85
        
    def test_threshold_monotonic(self):
        """Test that thresholds are in ascending order."""
        thresholds = [
            THRESHOLDS['upls_critical_low'],
            THRESHOLDS['upls_marginal'],
            THRESHOLDS['upls_acceptable'],
            THRESHOLDS['upls_strong']
        ]
        
        assert all(thresholds[i] < thresholds[i+1] for i in range(len(thresholds)-1))