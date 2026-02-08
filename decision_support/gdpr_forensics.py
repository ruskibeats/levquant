"""GDPR Forensics - Data integrity/iniquity risk indicator.

Court-safe assessment of potential data protection exposures.
Uses "potential exposure indicators" not absolute criminal assertions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional


@dataclass
class ForensicAssumptions:
    """Explicit assumptions for GDPR forensic model."""
    sar_gap_threshold_days: int = 30
    manual_override_severity: int = 3
    special_category_multiplier: float = 2.0
    model_version: str = "gdpr_forensics_v1.0"
    disclaimer: str = (
        "Potential exposure indicators only. "
        "Actual liability requires proof of intent and judicial determination."
    )


class GDPRForensics:
    """GDPR forensic analysis for data integrity risk.
    
    Court-safe language: "potential exposure indicators" not "proven violations".
    """
    
    # Risk scoring weights
    RISK_WEIGHTS = {
        "sar_gap_proven": 25,
        "manual_override_proven": 35,
        "special_category_involved": 20,
        "shadow_data_discovered": 15,
        "systemic_pattern": 15,
    }
    
    # Court-safe statutory liability descriptions
    STATUTORY_EXPOSURES = {
        "dpa_173": "Potential DPA 2018 s.173 exposure indicator (requires proof of intent)",
        "computer_misuse": "Potential Computer Misuse Act exposure indicator (fact-specific)",
        "article_5": "Potential Article 5(1)(d) accuracy obligation indicator",
        "article_9": "Potential Article 9 special category processing indicator",
        "article_12": "Potential Article 12(3) timely response indicator",
        "article_15": "Potential Article 15 access right indicator",
    }
    
    def __init__(self, assumptions: Optional[ForensicAssumptions] = None):
        self.assumptions = assumptions or ForensicAssumptions()
    
    def calculate_integrity_risk(
        self,
        sar_gap_proven: bool,
        manual_override_proven: bool,
        special_category_involved: bool = True,
        shadow_data_discovered: bool = True,
        systemic_pattern: bool = True,
    ) -> dict:
        """Calculate data integrity risk score.
        
        Args:
            sar_gap_proven: SAR shows gap in records
            manual_override_proven: Evidence of manual system override
            special_category_involved: Special category data present
            shadow_data_discovered: Unknown data holdings found
            systemic_pattern: Pattern suggests systemic issue
            
        Returns:
            Integrity risk analysis with court-safe language
        """
        # Calculate risk score
        risk_score = 0
        triggered_indicators = []
        
        if sar_gap_proven:
            risk_score += self.RISK_WEIGHTS["sar_gap_proven"]
            triggered_indicators.append("sar_gap_proven")
        
        if manual_override_proven:
            risk_score += self.RISK_WEIGHTS["manual_override_proven"]
            triggered_indicators.append("manual_override_proven")
        
        if special_category_involved:
            risk_score += self.RISK_WEIGHTS["special_category_involved"]
            triggered_indicators.append("special_category_involved")
        
        if shadow_data_discovered:
            risk_score += self.RISK_WEIGHTS["shadow_data_discovered"]
            triggered_indicators.append("shadow_data_discovered")
        
        if systemic_pattern:
            risk_score += self.RISK_WEIGHTS["systemic_pattern"]
            triggered_indicators.append("systemic_pattern")
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Determine statutory exposures
        statutory_exposures = self._identify_statutory_exposures(
            sar_gap_proven, manual_override_proven, special_category_involved
        )
        
        # Generate audit hash
        audit_data = {
            "sar_gap": sar_gap_proven,
            "manual_override": manual_override_proven,
            "special_category": special_category_involved,
            "shadow_data": shadow_data_discovered,
            "systemic": systemic_pattern,
            "score": risk_score,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        audit_hash = hashlib.sha256(
            json.dumps(audit_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "audit_hash": audit_hash,
            "model_version": self.assumptions.model_version,
            "assumptions": {
                "sar_gap_proven": sar_gap_proven,
                "manual_override_proven": manual_override_proven,
                "special_category_involved": special_category_involved,
                "shadow_data_discovered": shadow_data_discovered,
                "systemic_pattern": systemic_pattern,
                "risk_weights": self.RISK_WEIGHTS,
            },
            "integrity_risk": {
                "risk_score": risk_score,
                "risk_level": self._categorize_risk(risk_score),
                "triggered_indicators": triggered_indicators,
            },
            "statutory_exposures": statutory_exposures,
            "ico_reportable": risk_score >= 50,
            "ico_reportability_note": (
                "Likely reportable to ICO" if risk_score >= 50 
                else "Assessment required for reportability"
            ),
            "insurer_impact": self._assess_insurer_impact(risk_score, manual_override_proven),
            "court_safe_summary": self._generate_summary(risk_score, triggered_indicators),
            "disclaimer": self.assumptions.disclaimer,
        }
    
    def _identify_statutory_exposures(
        self,
        sar_gap_proven: bool,
        manual_override_proven: bool,
        special_category_involved: bool,
    ) -> list[dict]:
        """Identify potential statutory exposures with court-safe language."""
        exposures = []
        
        if manual_override_proven:
            exposures.append({
                "statute": "DPA 2018",
                "section": "s.173",
                "description": self.STATUTORY_EXPOSURES["dpa_173"],
                "severity": "high",
            })
            exposures.append({
                "statute": "Computer Misuse Act",
                "section": "s.1-3",
                "description": self.STATUTORY_EXPOSURES["computer_misuse"],
                "severity": "high",
            })
        
        if sar_gap_proven:
            exposures.append({
                "statute": "UK GDPR",
                "section": "Article 5(1)(d)",
                "description": self.STATUTORY_EXPOSURES["article_5"],
                "severity": "moderate",
            })
            exposures.append({
                "statute": "UK GDPR",
                "section": "Article 12(3)",
                "description": self.STATUTORY_EXPOSURES["article_12"],
                "severity": "moderate",
            })
            exposures.append({
                "statute": "UK GDPR",
                "section": "Article 15",
                "description": self.STATUTORY_EXPOSURES["article_15"],
                "severity": "moderate",
            })
        
        if special_category_involved:
            exposures.append({
                "statute": "UK GDPR",
                "section": "Article 9",
                "description": self.STATUTORY_EXPOSURES["article_9"],
                "severity": "high",
            })
        
        return exposures
    
    def _categorize_risk(self, score: int) -> str:
        """Categorize risk level."""
        if score >= 80:
            return "CRITICAL - Immediate assessment required"
        elif score >= 60:
            return "HIGH - Elevated exposure indicators"
        elif score >= 40:
            return "MODERATE - Multiple exposure indicators present"
        elif score >= 20:
            return "ELEVATED - Some exposure indicators"
        else:
            return "LOW - Limited exposure indicators"
    
    def _assess_insurer_impact(self, risk_score: int, manual_override: bool) -> dict:
        """Assess impact on insurance coverage."""
        if risk_score >= 70 and manual_override:
            return {
                "reservation_of_rights": "Elevated - Likely to be issued",
                "iniquity_exclusion": "Risk elevated (requires dishonesty finding)",
                "coverage_stress": "High",
                "recommendation": "Request coverage confirmation in writing",
            }
        elif risk_score >= 50:
            return {
                "reservation_of_rights": "Elevated",
                "iniquity_exclusion": "Under review",
                "coverage_stress": "Moderate",
                "recommendation": "Monitor insurer communications closely",
            }
        else:
            return {
                "reservation_of_rights": "Standard",
                "iniquity_exclusion": "Not triggered",
                "coverage_stress": "Low",
                "recommendation": "Standard notification procedures",
            }
    
    def _generate_summary(self, score: int, indicators: list[str]) -> str:
        """Generate court-safe summary."""
        level = self._categorize_risk(score)
        
        if not indicators:
            return (
                "Limited data integrity exposure indicators identified. "
                "Standard data protection compliance measures appear adequate."
            )
        
        indicator_text = ", ".join(ind.replace("_", " ") for ind in indicators[:3])
        
        return (
            f"Data integrity assessment indicates {level.lower()}. "
            f"Exposure indicators include: {indicator_text}. "
            f"These are analytical indicators requiring further evidential support."
        )


def quick_integrity_check(
    sar_gap_proven: bool = True,
    manual_override_proven: bool = True,
) -> dict:
    """Quick integrity check without full initialization."""
    forensics = GDPRForensics()
    return forensics.calculate_integrity_risk(
        sar_gap_proven=sar_gap_proven,
        manual_override_proven=manual_override_proven,
    )
