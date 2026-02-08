"""Tests for decision_support.gdpr_liability module."""

from __future__ import annotations

import pytest

from decision_support.gdpr_liability import (
    DataControllerExposure,
    GdprLiabilityPricer,
    create_hiloka_exposure,
    create_maven_exposure,
    HILOKA_GDPR_EXPOSURE,
    MAVEN_GDPR_EXPOSURE,
)


class TestGdprLiabilityPricer:
    """Tests for GdprLiabilityPricer."""

    def test_calculate_article_82_low_distress(self) -> None:
        """Test Article 82 calculation for low distress."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=1_000_000,
            data_subjects_affected=100,
            special_category_data=False,
            dsar_refused=False,
            shadow_data_discovered=False,
        )
        pricer = GdprLiabilityPricer(controller)
        result = pricer.calculate_article_82_exposure()
        
        assert result["distress_level"] == "low"
        assert result["total_exposure_low"] == 100 * 100  # 100 subjects × £100
        assert result["total_exposure_high"] == 100 * 500  # 100 subjects × £500

    def test_calculate_article_82_severe_distress(self) -> None:
        """Test Article 82 calculation for severe distress."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=1_000_000,
            data_subjects_affected=50,
            special_category_data=True,
            dsar_refused=True,
            shadow_data_discovered=True,
        )
        pricer = GdprLiabilityPricer(controller)
        result = pricer.calculate_article_82_exposure()
        
        assert result["distress_level"] == "severe"
        assert result["total_exposure_low"] == 50 * 5000
        assert result["total_exposure_high"] == 50 * 10000

    def test_calculate_ico_fine_minor(self) -> None:
        """Test ICO fine calculation for minor violations."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=10_000_000,
            data_subjects_affected=100,
            special_category_data=False,
            dsar_refused=False,
            shadow_data_discovered=False,
        )
        pricer = GdprLiabilityPricer(controller)
        result = pricer.calculate_ico_fine_exposure()
        
        assert result["fine_band"] == "minor"
        assert result["max_fine_calculated"] == 10_000_000 * 0.005  # 0.5%

    def test_calculate_ico_fine_serious(self) -> None:
        """Test ICO fine calculation for serious violations."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=10_000_000,
            data_subjects_affected=100,
            special_category_data=True,
            dsar_refused=True,
            shadow_data_discovered=True,
        )
        pricer = GdprLiabilityPricer(controller)
        result = pricer.calculate_ico_fine_exposure()
        
        assert result["fine_band"] == "serious"
        assert result["violations_identified"] >= 4
        # Should be max of 4% turnover or £17.5m
        expected_fine = max(10_000_000 * 0.04, 17_500_000)
        assert result["max_fine_calculated"] == expected_fine

    def test_shadow_data_risk_no_dsar(self) -> None:
        """Test shadow data risk when no DSAR refused."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=1_000_000,
            data_subjects_affected=100,
            special_category_data=False,
            dsar_refused=False,
            shadow_data_discovered=False,
        )
        pricer = GdprLiabilityPricer(controller)
        result = pricer.calculate_shadow_data_risk()
        
        assert result["risk_present"] is False

    def test_shadow_data_risk_critical(self) -> None:
        """Test shadow data risk with special category data."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=1_000_000,
            data_subjects_affected=100,
            special_category_data=True,
            dsar_refused=True,
            shadow_data_discovered=True,
        )
        pricer = GdprLiabilityPricer(controller)
        result = pricer.calculate_shadow_data_risk()
        
        assert result["risk_present"] is True
        assert result["risk_level"] == "CRITICAL"
        assert result["multiplier"] == 3.0

    def test_generate_total_exposure_report(self) -> None:
        """Test comprehensive exposure report generation."""
        controller = DataControllerExposure(
            controller_name="Test Controller",
            annual_turnover_gbp=5_000_000,
            data_subjects_affected=75,
            special_category_data=True,
            dsar_refused=True,
            shadow_data_discovered=True,
        )
        pricer = GdprLiabilityPricer(controller)
        report = pricer.generate_total_exposure_report()
        
        assert report["controller"] == "Test Controller"
        assert "article_82_exposure" in report
        assert "ico_fine_exposure" in report
        assert "shadow_data_risk" in report
        assert "combined_maximum_exposure" in report
        assert "tactical_insights" in report

    def test_tactical_insights_special_category(self) -> None:
        """Test tactical insights for special category data."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=1_000_000,
            data_subjects_affected=100,
            special_category_data=True,
            dsar_refused=False,
            shadow_data_discovered=False,
        )
        pricer = GdprLiabilityPricer(controller)
        insights = pricer._generate_tactical_insights()
        
        assert any("Article 9" in i for i in insights)

    def test_tactical_insights_dsar_refused(self) -> None:
        """Test tactical insights for DSAR refusal."""
        controller = DataControllerExposure(
            controller_name="Test",
            annual_turnover_gbp=1_000_000,
            data_subjects_affected=100,
            special_category_data=False,
            dsar_refused=True,
            shadow_data_discovered=False,
        )
        pricer = GdprLiabilityPricer(controller)
        insights = pricer._generate_tactical_insights()
        
        assert any("Article 82" in i for i in insights)
        assert any("ICO complaint" in i for i in insights)


class TestPreconfiguredExposures:
    """Tests for pre-configured exposure models."""

    def test_hiloka_exposure_structure(self) -> None:
        """Test Hiloka exposure model structure."""
        hiloka = create_hiloka_exposure()
        report = hiloka.generate_total_exposure_report()
        
        assert report["controller"] == "Hiloka Ltd"
        assert hiloka.controller.special_category_data is True
        assert hiloka.controller.dsar_refused is True

    def test_maven_exposure_structure(self) -> None:
        """Test Maven exposure model structure."""
        maven = create_maven_exposure()
        report = maven.generate_total_exposure_report()
        
        assert report["controller"] == "Maven Capital Partners"
        assert maven.controller.annual_turnover_gbp == 50_000_000

    def test_hiloka_significant_exposure(self) -> None:
        """Test that Hiloka has significant exposure."""
        report = HILOKA_GDPR_EXPOSURE.generate_total_exposure_report()
        
        # Hiloka should have substantial Article 82 exposure
        article_82 = report["article_82_exposure"]
        assert article_82["total_exposure_high"] > 200_000

    def test_maven_large_turnover_fine(self) -> None:
        """Test that Maven has large ICO fine exposure."""
        report = MAVEN_GDPR_EXPOSURE.generate_total_exposure_report()
        
        # Maven's £50m turnover × 2% = £1m potential fine (moderate band)
        ico_fine = report["ico_fine_exposure"]
        assert ico_fine["max_fine_calculated"] >= 1_000_000
