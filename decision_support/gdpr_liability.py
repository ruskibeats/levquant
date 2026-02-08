"""GDPR Liability Module - Quantify data subject exposure for Hiloka/Maven.

Models Article 82 damages, ICO regulatory fines, and shadow data discovery risk
post-DSAR refusal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class DataControllerExposure:
    """Exposure configuration for a data controller."""
    controller_name: str
    annual_turnover_gbp: float
    data_subjects_affected: int
    special_category_data: bool
    dsar_refused: bool
    shadow_data_discovered: bool


class GdprLiabilityPricer:
    """Prices GDPR liability exposure under UK GDPR and Data Protection Act 2018.
    
    Key exposures:
    - Article 82 non-material distress damages
    - ICO administrative fines (up to 4% global turnover)
    - Shadow data discovery (unknown holdings post-DSAR)
    """
    
    # ICO fine bands (simplified from GDPR Article 83)
    FINE_BANDS = {
        "minor": 0.005,      # 0.5% of turnover
        "moderate": 0.02,    # 2% of turnover  
        "serious": 0.04,     # 4% of turnover
    }
    
    # Article 82 distress damages (per data subject, based on case law)
    DISTRESS_RANGES = {
        "low": (100, 500),
        "moderate": (500, 2000),
        "high": (2000, 5000),
        "severe": (5000, 10000),
    }
    
    def __init__(self, controller: DataControllerExposure):
        self.controller = controller
        
    def calculate_article_82_exposure(self) -> dict:
        """Calculate Article 82 non-material distress damages.
        
        Based on UK case law (Vidal-Hall v Google, Lloyd v Google):
        - Low distress: £100-500 per subject
        - Moderate distress: £500-2,000 per subject
        - High distress: £2,000-5,000 per subject
        - Severe distress: £5,000-10,000 per subject
        
        Returns:
            Article 82 exposure analysis
        """
        subjects = self.controller.data_subjects_affected
        
        # Determine distress level based on severity factors
        distress_level = self._assess_distress_level()
        low, high = self.DISTRESS_RANGES[distress_level]
        
        return {
            "article": "Article 82 UK GDPR",
            "legal_basis": "Right to compensation for material/non-material damage",
            "data_subjects": subjects,
            "distress_level": distress_level,
            "per_subject_range": f"£{low:,} - £{high:,}",
            "total_exposure_low": subjects * low,
            "total_exposure_high": subjects * high,
            "notes": "Distress damages for unlawful processing and DSAR refusal",
        }
    
    def calculate_ico_fine_exposure(self) -> dict:
        """Calculate ICO administrative fine exposure.
        
        ICO can fine up to £17.5m or 4% global turnover (whichever higher)
        under GDPR Article 83(5) for serious infringements.
        
        Returns:
            ICO fine exposure analysis
        """
        turnover = self.controller.annual_turnover_gbp
        
        # Determine fine band based on violations
        violations = self._count_gdpr_violations()
        
        if violations >= 4:
            fine_band = "serious"
            max_fine = max(turnover * self.FINE_BANDS["serious"], 17_500_000)
        elif violations >= 2:
            fine_band = "moderate"
            max_fine = turnover * self.FINE_BANDS["moderate"]
        else:
            fine_band = "minor"
            max_fine = turnover * self.FINE_BANDS["minor"]
        
        return {
            "regulator": "Information Commissioner's Office (ICO)",
            "legal_basis": "Article 83(5) UK GDPR - Administrative fines",
            "annual_turnover": turnover,
            "fine_band": fine_band,
            "violations_identified": violations,
            "max_fine_calculated": max_fine,
            "fine_percentage": f"{self.FINE_BANDS[fine_band] * 100}%",
            "notes": "Fine for unlawful processing and failure to comply with DSAR",
        }
    
    def calculate_shadow_data_risk(self) -> dict:
        """Calculate shadow data discovery risk.
        
        Shadow data = data holdings discovered after DSAR that were
        not previously disclosed. Indicates systemic data governance failure.
        
        Returns:
            Shadow data risk analysis
        """
        if not self.controller.dsar_refused:
            return {
                "risk_present": False,
                "notes": "No DSAR refusal - standard data mapping applies",
            }
        
        # DSAR refusal with "special category data" admission = high risk
        base_exposure = self.controller.data_subjects_affected * 1000
        
        if self.controller.special_category_data:
            multiplier = 3.0  # Special category under Article 9
            risk_level = "CRITICAL"
        elif self.controller.shadow_data_discovered:
            multiplier = 2.5
            risk_level = "HIGH"
        else:
            multiplier = 1.5
            risk_level = "ELEVATED"
        
        return {
            "risk_present": True,
            "risk_level": risk_level,
            "legal_basis": "Article 5(1)(d) - Accuracy and data minimisation",
            "base_exposure": base_exposure,
            "adjusted_exposure": base_exposure * multiplier,
            "multiplier": multiplier,
            "special_category_involved": self.controller.special_category_data,
            "notes": "DSAR refusal suggests inadequate data mapping and potential systemic breach",
        }
    
    def generate_total_exposure_report(self) -> dict:
        """Generate comprehensive GDPR exposure report.
        
        Returns:
            Complete GDPR liability analysis
        """
        article_82 = self.calculate_article_82_exposure()
        ico_fine = self.calculate_ico_fine_exposure()
        shadow_data = self.calculate_shadow_data_risk()
        
        # Calculate total exposure range
        total_low = article_82["total_exposure_low"]
        total_high = article_82["total_exposure_high"]
        
        if shadow_data["risk_present"]:
            total_low += shadow_data["adjusted_exposure"]
            total_high += shadow_data["adjusted_exposure"]
        
        # ICO fine is separate (regulatory, not compensatory)
        ico_exposure = ico_fine["max_fine_calculated"]
        
        return {
            "controller": self.controller.controller_name,
            "analysis_date": "2026-02-08",
            "article_82_exposure": article_82,
            "ico_fine_exposure": ico_fine,
            "shadow_data_risk": shadow_data,
            "total_compensatory_exposure": {
                "low": total_low,
                "high": total_high,
            },
            "regulatory_fine_exposure": ico_exposure,
            "combined_maximum_exposure": total_high + ico_exposure,
            "tactical_insights": self._generate_tactical_insights(),
        }
    
    def _assess_distress_level(self) -> str:
        """Assess distress level based on violation severity."""
        if self.controller.special_category_data and self.controller.dsar_refused:
            return "severe"
        elif self.controller.special_category_data:
            return "high"
        elif self.controller.dsar_refused:
            return "moderate"
        else:
            return "low"
    
    def _count_gdpr_violations(self) -> int:
        """Count identified GDPR violations."""
        violations = 0
        
        if self.controller.dsar_refused:
            violations += 2  # Article 12(3) + Article 15
        if self.controller.special_category_data:
            violations += 1  # Article 9 processing
        if self.controller.shadow_data_discovered:
            violations += 1  # Article 5(1)(d) accuracy
            
        return violations
    
    def _generate_tactical_insights(self) -> List[str]:
        """Generate tactical insights for negotiators."""
        insights = []
        
        if self.controller.special_category_data:
            insights.append(
                "Special category data involved - ICO prioritises enforcement under Article 9"
            )
        
        if self.controller.dsar_refused:
            insights.append(
                "DSAR refusal creates standalone Article 82 claim for frustration/distress"
            )
            insights.append(
                "ICO complaint recommended - triggers regulatory timeline pressure"
            )
        
        if self.controller.shadow_data_discovered:
            insights.append(
                "Shadow data indicates systemic breach - class action risk elevated"
            )
        
        exposure = self.calculate_article_82_exposure()
        if exposure["total_exposure_high"] > 500_000:
            insights.append(
                f"£{exposure['total_exposure_high']/1e6:.1f}m+ Article 83 exposure - "
                "significant contingent liability for balance sheet"
            )
        
        return insights


def create_hiloka_exposure() -> GdprLiabilityPricer:
    """Create GDPR exposure model for Hiloka Ltd.
    
    Based on: Hiloka_NPCO_Letter_19May2025.pdf
    - DSAR refused (inside dealing)
    - Special category data admitted
    - Data subjects: ~50-100 (estimated from context)
    """
    hiloka = DataControllerExposure(
        controller_name="Hiloka Ltd",
        annual_turnover_gbp=5_000_000,  # Estimated from SME profile
        data_subjects_affected=75,  # Estimated
        special_category_data=True,
        dsar_refused=True,
        shadow_data_discovered=True,  # Admission of "sensitive" data
    )
    return GdprLiabilityPricer(hiloka)


def create_maven_exposure() -> GdprLiabilityPricer:
    """Create GDPR exposure model for Maven Capital Partners.
    
    Based on: RBatchelor 20260112 (1).pdf
    - DSAR refused
    - "Specialist legal advice" required
    - Sanjay Patel shadow director
    """
    maven = DataControllerExposure(
        controller_name="Maven Capital Partners",
        annual_turnover_gbp=50_000_000,  # PE firm estimate
        data_subjects_affected=500,  # Portfolio company contacts
        special_category_data=True,  # "Sensitive data" in refusal
        dsar_refused=True,
        shadow_data_discovered=False,  # Not yet confirmed
    )
    return GdprLiabilityPricer(maven)


# Pre-configured exposure models for immediate use
HILOKA_GDPR_EXPOSURE = create_hiloka_exposure()
MAVEN_GDPR_EXPOSURE = create_maven_exposure()
