"""
Output locks for scoring calculations.

This test locks the numbers. If this test ever fails, you stop.

This prevents "Cursor helpfully changed something" in the sacred math.
"""

import pytest
from engine.scoring import calculate_upls, calculate_tripwire, calculate_comprehensive_score


class TestScoringOutputs:
    """
    Lock the outputs of scoring calculations.
    
    These tests ensure that the scoring logic produces deterministic results.
    If any of these fail, the economics have changed.
    """
    
    def test_upls_calculation_baseline(self):
        """
        Test UPLS calculation with baseline values.
        
        Given SV1a=0.38, SV1b=0.86, SV1c=0.75
        UPLS must equal 0.641
        """
        sv1a = 0.38
        sv1b = 0.86
        sv1c = 0.75
        
        expected_upls = 0.641
        actual_upls = calculate_upls(sv1a, sv1b, sv1c)
        
        assert actual_upls == expected_upls, (
            f"UPLS calculation changed: expected {expected_upls}, "
            f"got {actual_upls}. If this is intentional, update the test."
        )
    
    def test_tripwire_calculation_baseline(self):
        """
        Test tripwire calculation with baseline UPLS.
        
        Given UPLS=0.641, base_multiplier=10.0
        Tripwire must equal 6.41
        """
        upls = 0.641
        base_multiplier = 10.0
        
        expected_tripwire = 6.41
        actual_tripwire = calculate_tripwire(upls, base_multiplier)
        
        assert actual_tripwire == expected_tripwire, (
            f"Tripwire calculation changed: expected {expected_tripwire}, "
            f"got {actual_tripwire}. If this is intentional, update the test."
        )
    
    def test_comprehensive_score_baseline(self):
        """
        Test comprehensive score calculation.
        
        Given SV1a=0.38, SV1b=0.86, SV1c=0.75
        UPLS must equal 0.641
        Tripwire must equal 6.41
        """
        sv1a = 0.38
        sv1b = 0.86
        sv1c = 0.75
        
        result = calculate_comprehensive_score(sv1a, sv1b, sv1c)
        
        expected_upls = 0.641
        expected_tripwire = 6.41
        
        assert result['upls'] == expected_upls, (
            f"UPLS calculation changed: expected {expected_upls}, "
            f"got {result['upls']}. If this is intentional, update the test."
        )
        
        assert result['tripwire'] == expected_tripwire, (
            f"Tripwire calculation changed: expected {expected_tripwire}, "
            f"got {result['tripwire']}. If this is intentional, update the test."
        )
    
    def test_upls_zero_values(self):
        """Test UPLS calculation with all zero values."""
        sv1a = 0.0
        sv1b = 0.0
        sv1c = 0.0
        
        expected_upls = 0.0
        actual_upls = calculate_upls(sv1a, sv1b, sv1c)
        
        assert actual_upls == expected_upls
    
    def test_upls_max_values(self):
        """Test UPLS calculation with all maximum values."""
        sv1a = 1.0
        sv1b = 1.0
        sv1c = 1.0
        
        expected_upls = 1.0
        actual_upls = calculate_upls(sv1a, sv1b, sv1c)
        
        assert actual_upls == expected_upls
    
    def test_upls_invalid_range(self):
        """Test that UPLS raises ValueError for invalid inputs."""
        with pytest.raises(ValueError, match="must be in range"):
            calculate_upls(1.5, 0.5, 0.5)
        
        with pytest.raises(ValueError, match="must be in range"):
            calculate_upls(0.5, -0.1, 0.5)
    
    def test_tripwire_invalid_range(self):
        """Test that tripwire raises ValueError for invalid UPLS."""
        with pytest.raises(ValueError, match="must be in range"):
            calculate_tripwire(1.5)
        
        with pytest.raises(ValueError, match="must be in range"):
            calculate_tripwire(-0.1)