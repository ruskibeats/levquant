"""Tests for decision_support/gdpr_forensics.py - GDPR Forensics module."""

from __future__ import annotations

import pytest

from decision_support.gdpr_forensics import (
    GDPRForensics,
    ForensicAssumptions,
    quick_integrity_check,
)


class TestGDPRForensics:
    """Tests for GDPRForensics model."""

    def test_low_risk_score(self) -> None:
        """Test low risk with no indicators."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=False,
            manual_override_proven=False,
            special_category_involved=False,
            shadow_data_discovered=False,
            systemic_pattern=False,
        )
        
        assert result["integrity_risk"]["risk_score"] == 0
        assert "LOW" in result["integrity_risk"]["risk_level"]

    def test_high_risk_with_manual_override(self) -> None:
        """Test high risk with manual override."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,
            special_category_involved=True,
            shadow_data_discovered=True,
            systemic_pattern=True,
        )
        
        assert result["integrity_risk"]["risk_score"] >= 60
        assert result["integrity_risk"]["risk_level"].startswith("HIGH") or \
               result["integrity_risk"]["risk_level"].startswith("CRITICAL")

    def test_ico_reportable_threshold(self) -> None:
        """Test ICO reportability at 50+ score."""
        forensics = GDPRForensics()
        
        # High score - should be reportable
        high = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,
            special_category_involved=False,
            shadow_data_discovered=False,
            systemic_pattern=False,
        )
        assert high["ico_reportable"] is True
        
        # Low score - should not be reportable
        low = forensics.calculate_integrity_risk(
            sar_gap_proven=False,
            manual_override_proven=False,
            special_category_involved=False,
            shadow_data_discovered=False,
            systemic_pattern=False,
        )
        assert low["ico_reportable"] is False

    def test_statutory_exposures_court_safe(self) -> None:
        """Test statutory exposures use court-safe language."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,
        )
        
        for exposure in result["statutory_exposures"]:
            desc = exposure["description"]
            assert "indicator" in desc.lower() or "potential" in desc.lower()
            assert "proven" not in desc.lower()
            assert "guilty" not in desc.lower()

    def test_insurer_impact_assessment(self) -> None:
        """Test insurer impact assessment."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,  # High risk
        )
        
        impact = result["insurer_impact"]
        assert "reservation_of_rights" in impact
        assert "iniquity_exclusion" in impact
        assert "coverage_stress" in impact

    def test_assumptions_echoed(self) -> None:
        """Test assumptions are echoed in output."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=False,
        )
        
        assert result["assumptions"]["sar_gap_proven"] is True
        assert result["assumptions"]["manual_override_proven"] is False

    def test_audit_hash_present(self) -> None:
        """Test audit hash is generated."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,
        )
        
        assert "audit_hash" in result
        assert len(result["audit_hash"]) == 16

    def test_disclaimer_present(self) -> None:
        """Test disclaimer is present."""
        forensics = GDPRForensics()
        result = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,
        )
        
        # Case-insensitive check for disclaimer content
        disclaimer_lower = result["disclaimer"].lower()
        assert "potential exposure indicators" in disclaimer_lower
        assert "requires proof" in disclaimer_lower

    def test_score_changes_with_toggles(self) -> None:
        """Test that score changes when toggles flip."""
        forensics = GDPRForensics()
        
        off = forensics.calculate_integrity_risk(
            sar_gap_proven=False,
            manual_override_proven=False,
        )
        on = forensics.calculate_integrity_risk(
            sar_gap_proven=True,
            manual_override_proven=True,
        )
        
        assert on["integrity_risk"]["risk_score"] > off["integrity_risk"]["risk_score"]


class TestQuickIntegrityCheck:
    """Tests for quick_integrity_check function."""

    def test_quick_check_returns_results(self) -> None:
        """Test quick check returns results."""
        result = quick_integrity_check(sar_gap_proven=True, manual_override_proven=True)
        
        assert "integrity_risk" in result
        assert result["assumptions"]["sar_gap_proven"] is True
