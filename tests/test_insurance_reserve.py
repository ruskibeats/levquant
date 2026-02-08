"""Tests for decision_support.insurance_reserve module."""

from __future__ import annotations

import pytest

from decision_support.insurance_reserve import (
    InsuranceReserveModel,
    calculate_settlement_with_reserve_pressure,
)


class TestInsuranceReserveModel:
    """Tests for InsuranceReserveModel."""

    def test_default_initialization(self) -> None:
        """Test default reserve model initialization."""
        model = InsuranceReserveModel()
        assert model.case_reserve == 2_000_000
        assert model.policy_limit == 10_000_000
        assert model.deductible == 250_000
        assert model.ibnr_percentage == 0.15

    def test_calculate_ibnr_exposure(self) -> None:
        """Test IBNR calculation."""
        model = InsuranceReserveModel(ibnr_percentage=0.15)
        ibnr = model.calculate_ibnr_exposure(5_000_000)
        assert ibnr == 750_000  # 15% of 5m

    def test_calculate_total_reserve(self) -> None:
        """Test total reserve calculation."""
        model = InsuranceReserveModel(case_reserve_gbp=2_000_000, ibnr_percentage=0.15)
        result = model.calculate_total_reserve(5_000_000)
        
        assert result["case_reserve"] == 2_000_000
        assert result["ibnr_reserve"] == 750_000
        assert result["total_reserve"] == 2_750_000
        assert result["headroom"] == 7_250_000  # 10m - 2.75m

    def test_calculate_reserve_gap_positive(self) -> None:
        """Test reserve gap when demand exceeds reserves."""
        model = InsuranceReserveModel(case_reserve_gbp=2_000_000)
        result = model.calculate_reserve_gap(5_000_000)
        
        assert result["reserve_gap"] > 0
        assert result["within_policy_limit"] is True
        assert result["reserve_adequate"] is False

    def test_calculate_reserve_gap_negative(self) -> None:
        """Test reserve gap when reserves exceed demand."""
        model = InsuranceReserveModel(case_reserve_gbp=10_000_000)
        result = model.calculate_reserve_gap(5_000_000)
        
        assert result["reserve_gap"] < 0
        assert result["reserve_adequate"] is True

    def test_check_coverage_stress_no_flags(self) -> None:
        """Test coverage stress with no flags."""
        model = InsuranceReserveModel()
        result = model.check_coverage_stress([])
        
        assert result["coverage_stress_score"] == 0.0
        assert result["stress_level"] == "NORMAL - Standard reserve position"
        assert result["iniquity_exclusion_risk"] is False

    def test_check_coverage_stress_high(self) -> None:
        """Test coverage stress with serious flags."""
        model = InsuranceReserveModel()
        result = model.check_coverage_stress([
            "sra_formal_action",
            "criminal_investigation_escalation",
        ])
        
        assert result["coverage_stress_score"] >= 0.5
        assert result["iniquity_exclusion_risk"] is True
        assert "sra_formal_action" in result["triggered_exclusions"]

    def test_check_coverage_stress_critical(self) -> None:
        """Test coverage stress with critical flags."""
        model = InsuranceReserveModel()
        result = model.check_coverage_stress([
            "sra_formal_action",
            "adverse_judicial_language",
            "criminal_investigation_escalation",
            "shadow_director_proven",
        ])
        
        assert result["coverage_stress_score"] >= 0.7
        assert result["stress_level"] == "CRITICAL - Coverage voidance likely"

    def test_generate_reserve_report_structure(self) -> None:
        """Test reserve report structure."""
        model = InsuranceReserveModel()
        report = model.generate_reserve_report(5_000_000, [])
        
        assert "reserve_position" in report
        assert "gap_analysis" in report
        assert "coverage_stress" in report
        assert "negotiation_leverage" in report
        assert "tactical_recommendations" in report

    def test_leverage_score_calculation(self) -> None:
        """Test leverage score with reserve gap."""
        model = InsuranceReserveModel(case_reserve_gbp=1_000_000)
        report = model.generate_reserve_report(7_000_000, [])
        
        leverage = report["negotiation_leverage"]
        assert leverage["score"] > 0
        assert "rating" in leverage
        assert "key_insight" in leverage

    def test_tactical_recommendations_stress(self) -> None:
        """Test tactical recommendations under stress."""
        model = InsuranceReserveModel()
        report = model.generate_reserve_report(5_000_000, [
            "sra_formal_action",
            "criminal_investigation_escalation",
        ])
        
        tactics = report["tactical_recommendations"]
        assert len(tactics) > 0
        assert any("personal liability" in t.lower() for t in tactics)


class TestSettlementWithReservePressure:
    """Tests for settlement calculation with reserve pressure."""

    def test_base_settlement_unchanged_with_no_leverage(self) -> None:
        """Test that base settlement is unchanged when no leverage."""
        model = InsuranceReserveModel(case_reserve_gbp=10_000_000)
        result = calculate_settlement_with_reserve_pressure(5_000_000, model, [])
        
        assert result["base_settlement"] == 5_000_000
        assert result["leverage_multiplier"] == 1.0
        assert result["reserve_adjusted_settlement"] == 5_000_000

    def test_settlement_increases_with_leverage(self) -> None:
        """Test that settlement increases with leverage."""
        model = InsuranceReserveModel(case_reserve_gbp=1_000_000)
        result = calculate_settlement_with_reserve_pressure(5_000_000, model, [
            "sra_formal_action",
            "criminal_investigation_escalation",
        ])
        
        assert result["leverage_multiplier"] > 1.0
        assert result["reserve_adjusted_settlement"] > 5_000_000

    def test_settlement_capped_at_policy_limit(self) -> None:
        """Test that recommended demand is capped at policy limit."""
        model = InsuranceReserveModel(policy_limit_gbp=8_000_000)
        result = calculate_settlement_with_reserve_pressure(10_000_000, model, [])
        
        assert result["recommended_demand"] <= 8_000_000
