"""Tests for decision_support/insurance_shadow.py - Insurance Shadow Reserve module."""

from __future__ import annotations

import pytest

from decision_support.insurance_shadow import (
    InsuranceShadowReserve,
    ShadowReserveAssumptions,
    quick_shadow_check,
)


class TestInsuranceShadowReserve:
    """Tests for InsuranceShadowReserve model."""

    def test_reserve_increases_with_stage(self) -> None:
        """Test that reserve increases with litigation stage."""
        shadow = InsuranceShadowReserve()
        
        notification = shadow.calculate_shadow_reserve(5_000_000, "notification")
        defence = shadow.calculate_shadow_reserve(5_000_000, "defence_filed")
        procedural = shadow.calculate_shadow_reserve(5_000_000, "procedural_irregularity_flagged")
        trial = shadow.calculate_shadow_reserve(5_000_000, "trial_listed")
        
        n_reserve = notification["shadow_reserve"]["estimated_reserve_locked_gbp"]
        d_reserve = defence["shadow_reserve"]["estimated_reserve_locked_gbp"]
        p_reserve = procedural["shadow_reserve"]["estimated_reserve_locked_gbp"]
        t_reserve = trial["shadow_reserve"]["estimated_reserve_locked_gbp"]
        
        assert n_reserve < d_reserve < p_reserve < t_reserve

    def test_reserve_scales_with_claim_value(self) -> None:
        """Test that reserve scales with claim value."""
        shadow = InsuranceShadowReserve()
        
        small = shadow.calculate_shadow_reserve(1_000_000, "procedural_irregularity_flagged")
        large = shadow.calculate_shadow_reserve(10_000_000, "procedural_irregularity_flagged")
        
        small_reserve = small["shadow_reserve"]["estimated_reserve_locked_gbp"]
        large_reserve = large["shadow_reserve"]["estimated_reserve_locked_gbp"]
        
        assert large_reserve == small_reserve * 10  # Linear scaling

    def test_dead_money_cost_calculated(self) -> None:
        """Test dead money cost calculation."""
        shadow = InsuranceShadowReserve()
        result = shadow.calculate_shadow_reserve(5_000_000, "procedural_irregularity_flagged")
        
        locked = result["shadow_reserve"]["estimated_reserve_locked_gbp"]
        annual = result["dead_money_cost"]["annual_cost_gbp"]
        
        # Annual cost should be ~6% of locked capital
        expected = locked * 0.06
        assert abs(annual - expected) < 1  # Allow for rounding

    def test_stage_progression_calculated(self) -> None:
        """Test stage progression analysis."""
        shadow = InsuranceShadowReserve()
        progression = shadow.calculate_stage_progression(
            5_000_000,
            "notification",
            "trial_listed"
        )
        
        assert progression["current_stage"] == "notification"
        assert progression["target_stage"] == "trial_listed"
        assert progression["reserve_increase_gbp"] > 0

    def test_negotiation_lever_generated(self) -> None:
        """Test negotiation lever is generated."""
        shadow = InsuranceShadowReserve()
        result = shadow.calculate_shadow_reserve(5_000_000, "trial_listed")
        
        lever = result["negotiation_lever"]
        assert "lever_strength" in lever
        assert "rationale" in lever
        assert "suggested_tactic" in lever

    def test_illustrative_disclaimer_present(self) -> None:
        """Test illustrative disclaimer is present."""
        shadow = InsuranceShadowReserve()
        result = shadow.calculate_shadow_reserve(5_000_000, "procedural_irregularity_flagged")
        
        # Case-insensitive check
        note_lower = result["illustrative_note"].lower()
        assert "illustrative" in note_lower
        assert "not actual insurer" in note_lower

    def test_assumptions_echoed(self) -> None:
        """Test assumptions are echoed in output."""
        shadow = InsuranceShadowReserve()
        result = shadow.calculate_shadow_reserve(7_000_000, "defence_filed")
        
        assert result["assumptions"]["claim_value_gbp"] == 7_000_000
        assert result["assumptions"]["litigation_stage"] == "defence_filed"

    def test_audit_hash_present(self) -> None:
        """Test audit hash is generated."""
        shadow = InsuranceShadowReserve()
        result = shadow.calculate_shadow_reserve(5_000_000, "procedural_irregularity_flagged")
        
        assert "audit_hash" in result
        assert len(result["audit_hash"]) == 16

    def test_court_safe_summary(self) -> None:
        """Test court-safe summary language."""
        shadow = InsuranceShadowReserve()
        result = shadow.calculate_shadow_reserve(5_000_000, "procedural_irregularity_flagged")
        
        summary = result["court_safe_summary"]
        assert "illustrative" in summary.lower() or "analysis" in summary.lower()
        assert "not an actual insurer" in summary.lower()


class TestQuickShadowCheck:
    """Tests for quick_shadow_check function."""

    def test_quick_check_returns_results(self) -> None:
        """Test quick check returns results."""
        result = quick_shadow_check(5_000_000, "procedural_irregularity_flagged")
        
        assert "shadow_reserve" in result
        assert result["assumptions"]["litigation_stage"] == "procedural_irregularity_flagged"

    def test_quick_check_uses_defaults(self) -> None:
        """Test quick check uses default values."""
        result = quick_shadow_check()
        
        assert result["assumptions"]["claim_value_gbp"] == 5_000_000
        assert result["assumptions"]["litigation_stage"] == "procedural_irregularity_flagged"
