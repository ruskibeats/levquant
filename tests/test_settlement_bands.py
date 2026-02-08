"""Tests for decision_support.settlement_bands module.

Three-band system constraints:
- BASE: £2.5m–£4m (0 flags)
- VALIDATION: £5m–£9m (1 flag)
- TAIL: £12m–£15m (≥2 flags)
- £15m appears ONLY in TAIL
- No speculative inflation
"""

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

    def test_base_band_range(self) -> None:
        """BASE band must be £2.5m–£4m."""
        assert BAND_DEFINITIONS["BASE"].minimum_gbp == 2_500_000
        assert BAND_DEFINITIONS["BASE"].maximum_gbp == 4_000_000

    def test_validation_band_range(self) -> None:
        """VALIDATION band must be £5m–£9m."""
        assert BAND_DEFINITIONS["VALIDATION"].minimum_gbp == 5_000_000
        assert BAND_DEFINITIONS["VALIDATION"].maximum_gbp == 9_000_000

    def test_tail_band_range(self) -> None:
        """TAIL band must be £12m–£15m."""
        assert BAND_DEFINITIONS["TAIL"].minimum_gbp == 12_000_000
        assert BAND_DEFINITIONS["TAIL"].maximum_gbp == 15_000_000

    def test_fifteen_million_only_in_tail(self) -> None:
        """£15m must appear ONLY in TAIL band."""
        for band_key, config in BAND_DEFINITIONS.items():
            if band_key == "TAIL":
                assert config.maximum_gbp == 15_000_000, "TAIL must cap at £15m"
            else:
                assert config.maximum_gbp < 15_000_000, f"{band_key} must not reach £15m"

    def test_base_does_not_exceed_four_million(self) -> None:
        """BASE must not exceed £4m."""
        assert BAND_DEFINITIONS["BASE"].maximum_gbp <= 4_000_000

    def test_validation_does_not_exceed_nine_million(self) -> None:
        """VALIDATION must not exceed £9m."""
        assert BAND_DEFINITIONS["VALIDATION"].maximum_gbp <= 9_000_000

    def test_bands_increase_in_value(self) -> None:
        """Each band must have higher minimum than previous."""
        assert BAND_DEFINITIONS["BASE"].maximum_gbp < BAND_DEFINITIONS["VALIDATION"].minimum_gbp
        assert BAND_DEFINITIONS["VALIDATION"].maximum_gbp < BAND_DEFINITIONS["TAIL"].minimum_gbp

    def test_base_requires_zero_flags(self) -> None:
        """BASE requires no flags."""
        assert BAND_DEFINITIONS["BASE"].required_flag_count == 0
        assert BAND_DEFINITIONS["BASE"].activation_flags == []

    def test_validation_requires_one_flag(self) -> None:
        """VALIDATION requires exactly 1 flag."""
        assert BAND_DEFINITIONS["VALIDATION"].required_flag_count == 1
        assert len(BAND_DEFINITIONS["VALIDATION"].activation_flags) >= 1

    def test_tail_requires_two_or_more_flags(self) -> None:
        """TAIL requires ≥2 flags."""
        assert BAND_DEFINITIONS["TAIL"].required_flag_count == 2


class TestSettlementBandCalculator:
    """Tests for SettlementBandCalculator - binary logic only."""

    def test_no_flags_returns_base(self) -> None:
        """No active flags should return BASE band."""
        calc = SettlementBandCalculator([])
        assert calc.current_band == "BASE"

    def test_one_validation_flag_returns_validation(self) -> None:
        """One validation flag should return VALIDATION band."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        assert calc.current_band == "VALIDATION"

    def test_two_tail_flags_returns_tail(self) -> None:
        """Two tail flags should return TAIL band."""
        calc = SettlementBandCalculator([
            "adverse_judicial_language",
            "sra_formal_action"
        ])
        assert calc.current_band == "TAIL"

    def test_three_tail_flags_returns_tail(self) -> None:
        """Three tail flags should still return TAIL band."""
        calc = SettlementBandCalculator([
            "adverse_judicial_language",
            "sra_formal_action",
            "insurance_coverage_stress"
        ])
        assert calc.current_band == "TAIL"

    def test_validation_flags_do_not_trigger_tail(self) -> None:
        """Validation flags alone should not trigger TAIL."""
        calc = SettlementBandCalculator([
            "judicial_comment_on_record",
            "sra_investigation_open"
        ])
        # Two VALIDATION flags still = VALIDATION, not TAIL
        assert calc.current_band == "VALIDATION"

    def test_mixed_flags_with_two_tail_returns_tail(self) -> None:
        """Mixed flags with 2 tail flags should return TAIL."""
        calc = SettlementBandCalculator([
            "judicial_comment_on_record",  # validation
            "adverse_judicial_language",   # tail
            "sra_formal_action"            # tail
        ])
        assert calc.current_band == "TAIL"

    def test_get_band_config_returns_correct_config(self) -> None:
        """get_band_config returns correct band configuration."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        config = calc.get_band_config()
        assert config.name == "Validation Settlement Band"
        assert config.minimum_gbp == 5_000_000

    def test_what_moves_up_from_base(self) -> None:
        """From BASE, what moves up should point to VALIDATION."""
        calc = SettlementBandCalculator([])
        what_moves = calc.get_what_moves_up()
        
        assert what_moves["next_band"] == "VALIDATION"
        assert what_moves["flags_needed"] == 1
        assert "£5.0m–£9.0m" in what_moves["next_range"]

    def test_what_moves_up_from_validation(self) -> None:
        """From VALIDATION, what moves up should point to TAIL."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        what_moves = calc.get_what_moves_up()
        
        assert what_moves["next_band"] == "TAIL"
        assert what_moves["flags_needed"] == 2  # Need 2 tail flags
        assert "£12.0m–£15.0m" in what_moves["next_range"]

    def test_what_moves_up_at_tail(self) -> None:
        """At TAIL, what moves up should indicate maximum reached."""
        calc = SettlementBandCalculator([
            "adverse_judicial_language",
            "sra_formal_action"
        ])
        what_moves = calc.get_what_moves_up()
        
        assert what_moves["next_band"] is None
        assert "maximum" in what_moves["message"].lower()

    def test_generate_band_summary_structure(self) -> None:
        """Band summary has expected structure."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        summary = calc.generate_band_summary()
        
        assert "current_band" in summary
        assert "current_band_name" in summary
        assert "current_range" in summary
        assert "minimum_gbp" in summary
        assert "maximum_gbp" in summary
        assert "meaning" in summary
        assert "what_moves_up" in summary
        assert "inactive_bands" in summary


class TestSettlementLetter:
    """Tests for settlement letter generation - court-safe language."""

    def test_letter_contains_band_name(self) -> None:
        """Generated letter contains current band name."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "Validation Settlement Band" in letter
        assert "CURRENT SETTLEMENT BAND" in letter

    def test_letter_contains_settlement_amounts(self) -> None:
        """Generated letter contains settlement amounts."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "£5,000,000" in letter or "£5.0m" in letter
        assert "£9,000,000" in letter or "£9.0m" in letter

    def test_letter_contains_what_moves_up(self) -> None:
        """Generated letter contains 'what moves up' section."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "WHAT MOVES THIS UP A BAND?" in letter

    def test_letter_without_prejudice_header(self) -> None:
        """Generated letter has without prejudice header."""
        calc = SettlementBandCalculator([])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "WITHOUT PREJUDICE" in letter

    def test_letter_contains_methodology_note(self) -> None:
        """Generated letter contains band methodology note."""
        calc = SettlementBandCalculator([])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        assert "Band Methodology Note" in letter
        assert "£12.0m–£15.0m" in letter  # TAIL band shown

    def test_letter_uses_court_safe_language(self) -> None:
        """Letter uses court-safe language, not advocacy."""
        calc = SettlementBandCalculator(["adverse_judicial_language", "sra_formal_action"])
        letter = generate_settlement_letter_banded(
            calc, "Claimant", "Respondent", "CASE-001", 1_000_000
        )
        
        # Should use procedural terms
        assert "procedural" in letter.lower() or "external validation" in letter.lower()
        
        # Should NOT use absolute claims
        assert "fraud proven" not in letter.lower()
        assert "guaranteed" not in letter.lower()


class TestWhatMovesUpExplanation:
    """Tests for 'What Moves This Up a Band?' explainer panel."""

    def test_explanation_contains_current_band(self) -> None:
        """Explanation mentions current band."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Validation Settlement Band" in explanation
        assert "Active Flags: 1" in explanation

    def test_explanation_contains_next_band(self) -> None:
        """Explanation mentions next band when applicable."""
        calc = SettlementBandCalculator(["judicial_comment_on_record"])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Tail Risk Settlement Band" in explanation
        assert "£12.0m–£15.0m" in explanation

    def test_explanation_shows_missing_flags(self) -> None:
        """Explanation shows missing flags."""
        calc = SettlementBandCalculator([])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Missing Flags" in explanation
        assert "☐" in explanation  # Checkbox for missing flags

    def test_explanation_at_tail(self) -> None:
        """Explanation at TAIL band shows status."""
        calc = SettlementBandCalculator([
            "adverse_judicial_language",
            "sra_formal_action"
        ])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Maximum band achieved" in explanation

    def test_explanation_includes_band_logic(self) -> None:
        """Explanation includes band logic summary."""
        calc = SettlementBandCalculator([])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "Band Logic Summary" in explanation
        assert "BASE (0 flags)" in explanation
        assert "VALIDATION (1 flag)" in explanation
        assert "TAIL (≥2 flags)" in explanation

    def test_explanation_notes_fifteen_million_is_tail_only(self) -> None:
        """Explanation explicitly notes £15m is TAIL only."""
        calc = SettlementBandCalculator([])
        explanation = get_what_moves_up_explanation(calc)
        
        assert "£15m is TAIL band only" in explanation
        assert "existential containment" in explanation.lower()
