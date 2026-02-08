"""Tests for decision_support.settlement_bands module."""

from __future__ import annotations

import pytest

from decision_support.settlement_bands import (
    BAND_DEFINITIONS,
    SettlementBandCalculator,
    generate_settlement_letter_banded,
    get_what_moves_up_explanation,
)


class TestBandDefinitions:
    """Tests for band configuration definitions."""

    def test_all_bands_have_required_fields(self) -> None:
        """All band definitions must have required fields."""
        for band_key, config in BAND_DEFINITIONS.items():
            assert config.name
            assert config.minimum_gbp >= 0
            assert config.typical_gbp >= config.minimum_gbp
            assert config.description
            assert config.required_flag_count >= 0
            assert config.unlock_message

    def test_bands_increase_in_value(self) -> None:
        """Each band must have higher minimum than previous."""
        band_order = ["BASE", "BAND_1", "BAND_2", "BAND_3", "MAXIMUM"]
        prev_min = 0
        
        for band_key in band_order:
            config = BAND_DEFINITIONS[band_key]
            assert config.minimum_gbp > prev_min
            prev_min = config.minimum_gbp

    def test_base_band_requires_zero_flags(self) -> None:
        """BASE band requires no flags."""
        assert BAND_DEFINITIONS["BASE"].required_flag_count == 0
        assert BAND_DEFINITIONS["BASE"].activation_flags == []

    def test_maximum_band_requires_eight_flags(self) -> None:
        """MAXIMUM band requires 8 flags."""
        assert BAND_DEFINITIONS["MAXIMUM"].required_flag_count == 8


class TestSettlementBandCalculator:
    """Tests for SettlementBandCalculator."""

    def test_no_flags_returns_base(self) -> None:
        """No active flags should return BASE band."""
        calc = SettlementBandCalculator([])
        assert calc.current_band == "BASE"

    def test_one_flag_returns_band_1(self) -> None:
        """One flag should return BAND_1."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        assert calc.current_band == "BAND_1"

    def test_three_flags_returns_band_2(self) -> None:
        """Three flags should return BAND_2."""
        calc = SettlementBandCalculator([
            "defence_nullity_confirmed",
            "sra_investigation_open",
            "insurer_notified_of_fraud"
        ])
        assert calc.current_band == "BAND_2"

    def test_four_flags_returns_band_3(self) -> None:
        """Four flags should return BAND_3."""
        calc = SettlementBandCalculator([
            "defence_nullity_confirmed",
            "sra_investigation_open",
            "insurer_notified_of_fraud",
            "administrative_override_admitted"
        ])
        assert calc.current_band == "BAND_3"

    def test_five_flags_returns_maximum(self) -> None:
        """Five flags should return MAXIMUM band."""
        calc = SettlementBandCalculator([
            "defence_nullity_confirmed",
            "sra_investigation_open",
            "insurer_notified_of_fraud",
            "administrative_override_admitted",
            "shadow_director_established"
        ])
        assert calc.current_band == "MAXIMUM"

    def test_get_band_config_returns_correct_config(self) -> None:
        """get_band_config returns correct band configuration."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        config = calc.get_band_config()
        assert config.name == "Elevated Risk Band"
        assert config.minimum_gbp == 1_500_000

    def test_flags_needed_for_next_band(self) -> None:
        """Calculate flags needed for next band."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        needed = calc.flags_needed_for_next_band()
        
        assert needed["next_band"] == "BAND_2"
        assert needed["flags_needed"] == 3  # Need 3 more flags to reach 4

    def test_next_band_none_at_maximum(self) -> None:
        """At MAXIMUM, next band should be None."""
        calc = SettlementBandCalculator([
            "defence_nullity_confirmed",
            "sra_investigation_open",
            "insurer_notified_of_fraud",
            "administrative_override_admitted",
            "shadow_director_established"
        ])
        assert calc.next_band is None
        needed = calc.flags_needed_for_next_band()
        assert needed["message"] == "Already at maximum band"

    def test_generate_band_summary_structure(self) -> None:
        """Band summary has expected structure."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        summary = calc.generate_band_summary()
        
        assert "current_band" in summary
        assert "current_band_name" in summary
        assert "minimum_settlement" in summary
        assert "typical_settlement" in summary
        assert "active_flags" in summary
        assert "what_moves_up" in summary
        assert "unlock_requirements" in summary


class TestSettlementLetter:
    """Tests for settlement letter generation."""

    def test_letter_contains_band_name(self) -> None:
        """Generated letter contains current band name."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "Elevated Risk Band" in letter
        assert "CURRENT SETTLEMENT BAND" in letter

    def test_letter_contains_settlement_amounts(self) -> None:
        """Generated letter contains settlement amounts."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        config = calc.get_band_config()
        assert f"£{config.minimum_gbp:,.0f}" in letter
        assert f"£{config.typical_gbp:,.0f}" in letter

    def test_letter_contains_flag_analysis(self) -> None:
        """Generated letter contains flag analysis section."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "FLAG ANALYSIS" in letter
        assert "Defence Nullity Confirmed" in letter

    def test_letter_contains_what_moves_up(self) -> None:
        """Generated letter contains 'what moves up' section."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "WHAT MOVES US UP A BAND?" in letter

    def test_letter_without_prejudice_header(self) -> None:
        """Generated letter has without prejudice header."""
        calc = SettlementBandCalculator([])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "WITHOUT PREJUDICE" in letter


class TestWhatMovesUpExplanation:
    """Tests for 'what moves up' explainer."""

    def test_explanation_contains_current_band(self) -> None:
        """Explanation mentions current band."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Elevated Risk Band" in explanation
        assert "Active Flags: 1" in explanation

    def test_explanation_contains_next_band(self) -> None:
        """Explanation mentions next band when applicable."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Serious Misconduct Band" in explanation
        assert "Required Flags: 4" in explanation

    def test_explanation_shows_missing_flags(self) -> None:
        """Explanation shows missing flags."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Missing Flags:" in explanation
        # Should show unchecked flags
        assert "☐" in explanation

    def test_explanation_at_maximum(self) -> None:
        """Explanation at maximum band shows status."""
        calc = SettlementBandCalculator([
            "defence_nullity_confirmed",
            "sra_investigation_open",
            "insurer_notified_of_fraud",
            "administrative_override_admitted",
            "shadow_director_established"
        ])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Maximum band achieved" in explanation
        assert "No higher band exists" in explanation

    def test_explanation_includes_band_logic(self) -> None:
        """Explanation includes band logic summary."""
        calc = SettlementBandCalculator(["defence_nullity_confirmed"])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Band Logic:" in explanation
        assert "BASE (0 flags)" in explanation
        assert "MAXIMUM (5 flags)" in explanation
