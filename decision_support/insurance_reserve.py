"""Insurance Reserve Model - Quantify insurer-specific reserve behaviors.

Models case reserves, IBNR exposure, and coverage stress triggers for
negotiation leverage calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReserveConfiguration:
    """Configuration for insurer reserve modeling."""
    case_reserve_gbp: float
    policy_limit_gbp: float
    deductible_gbp: float
    ibnr_percentage: float  # Incurred But Not Reported reserve %
    coverage_stress_threshold: float  # When iniquity exclusion triggers


class InsuranceReserveModel:
    """Models insurer reserve behaviors and coverage stress.
    
    Calculates the gap between actual reserves and exposure,
    which represents negotiation leverage.
    """
    
    def __init__(
        self,
        case_reserve_gbp: float = 2_000_000,  # Typical initial reserve
        policy_limit_gbp: float = 10_000_000,
        deductible_gbp: float = 250_000,
        ibnr_percentage: float = 0.15,  # 15% IBNR typical for litigation
    ):
        self.case_reserve = case_reserve_gbp
        self.policy_limit = policy_limit_gbp
        self.deductible = deductible_gbp
        self.ibnr_percentage = ibnr_percentage
        
    def calculate_ibnr_exposure(self, settlement_exposure_gbp: float) -> float:
        """Calculate Incurred But Not Reported reserve.
        
        IBNR represents reserves for claims that have occurred but not yet
        been reported or fully quantified. In systemic litigation issues,
        this can be significant.
        
        Args:
            settlement_exposure_gbp: Current settlement band exposure
            
        Returns:
            IBNR reserve amount
        """
        return settlement_exposure_gbp * self.ibnr_percentage
    
    def calculate_total_reserve(self, settlement_exposure_gbp: float) -> dict:
        """Calculate total reserve position.
        
        Returns:
            Dictionary with case reserve, IBNR, and total
        """
        ibnr = self.calculate_ibnr_exposure(settlement_exposure_gbp)
        total = self.case_reserve + ibnr
        
        return {
            "case_reserve": self.case_reserve,
            "ibnr_reserve": ibnr,
            "total_reserve": total,
            "policy_limit": self.policy_limit,
            "headroom": self.policy_limit - total,
        }
    
    def calculate_reserve_gap(self, settlement_demand_gbp: float) -> dict:
        """Calculate gap between reserves and settlement demand.
        
        This is the key negotiation leverage metric. A large gap means
        the insurer must increase reserves or face coverage stress.
        
        Args:
            settlement_demand_gbp: Current settlement demand
            
        Returns:
            Gap analysis dictionary
        """
        reserve_data = self.calculate_total_reserve(settlement_demand_gbp)
        gap = settlement_demand_gbp - reserve_data["total_reserve"]
        
        return {
            "settlement_demand": settlement_demand_gbp,
            "total_reserve": reserve_data["total_reserve"],
            "reserve_gap": gap,
            "gap_percentage": (gap / reserve_data["total_reserve"] * 100) if reserve_data["total_reserve"] > 0 else 0,
            "within_policy_limit": settlement_demand_gbp <= self.policy_limit,
            "reserve_adequate": gap <= 0,
        }
    
    def check_coverage_stress(self, active_flags: list[str]) -> dict:
        """Check if coverage stress triggers are activated.
        
        Coverage stress occurs when:
        1. Iniquity/fraud exclusion may apply
        2. Reserve gap is significant
        3. Policy limits approach
        
        Args:
            active_flags: List of active evidence flags
            
        Returns:
            Coverage stress analysis
        """
        stress_triggers = {
            "sra_formal_action": 0.3,
            "adverse_judicial_language": 0.25,
            "criminal_investigation_escalation": 0.4,
            "shadow_director_proven": 0.2,
            "metadata_12june_creation": 0.15,
        }
        
        stress_score = 0.0
        triggered_exclusions = []
        
        for flag in active_flags:
            if flag in stress_triggers:
                stress_score += stress_triggers[flag]
                triggered_exclusions.append(flag)
        
        # Cap at 1.0 (100% stress)
        stress_score = min(stress_score, 1.0)
        
        return {
            "coverage_stress_score": stress_score,
            "stress_level": self._categorize_stress(stress_score),
            "triggered_exclusions": triggered_exclusions,
            "iniquity_exclusion_risk": stress_score > 0.5,
            "reserve_escalation_required": stress_score > 0.3,
        }
    
    def _categorize_stress(self, stress_score: float) -> str:
        """Categorize coverage stress level."""
        if stress_score >= 0.7:
            return "CRITICAL - Coverage voidance likely"
        elif stress_score >= 0.5:
            return "HIGH - Iniquity exclusion triggered"
        elif stress_score >= 0.3:
            return "ELEVATED - Reserve escalation required"
        elif stress_score > 0:
            return "MODERATE - Monitor closely"
        else:
            return "NORMAL - Standard reserve position"
    
    def generate_reserve_report(
        self,
        settlement_demand_gbp: float,
        active_flags: list[str],
    ) -> dict:
        """Generate comprehensive reserve analysis report.
        
        Args:
            settlement_demand_gbp: Current settlement demand
            active_flags: Active evidence flags
            
        Returns:
            Complete reserve analysis
        """
        reserve_data = self.calculate_total_reserve(settlement_demand_gbp)
        gap_analysis = self.calculate_reserve_gap(settlement_demand_gbp)
        stress_analysis = self.check_coverage_stress(active_flags)
        
        # Calculate negotiation leverage
        leverage_score = 0.0
        if gap_analysis["reserve_gap"] > 0:
            leverage_score += min(gap_analysis["reserve_gap"] / 1_000_000, 5.0)  # Cap at 5 points
        if stress_analysis["iniquity_exclusion_risk"]:
            leverage_score += 3.0
        if not gap_analysis["within_policy_limit"]:
            leverage_score += 2.0
            
        return {
            "reserve_position": reserve_data,
            "gap_analysis": gap_analysis,
            "coverage_stress": stress_analysis,
            "negotiation_leverage": {
                "score": leverage_score,
                "rating": self._categorize_leverage(leverage_score),
                "key_insight": self._generate_leverage_insight(gap_analysis, stress_analysis),
            },
            "tactical_recommendations": self._generate_tactics(gap_analysis, stress_analysis),
        }
    
    def _categorize_leverage(self, score: float) -> str:
        """Categorize negotiation leverage."""
        if score >= 7:
            return "MAXIMUM - Insurer in crisis mode"
        elif score >= 5:
            return "HIGH - Significant reserve pressure"
        elif score >= 3:
            return "MODERATE - Standard negotiation position"
        elif score > 0:
            return "LIMITED - Reserve adequate"
        else:
            return "NONE - No leverage from reserves"
    
    def _generate_leverage_insight(
        self,
        gap_analysis: dict,
        stress_analysis: dict,
    ) -> str:
        """Generate key insight for negotiators."""
        gap = gap_analysis["reserve_gap"]
        
        if stress_analysis["iniquity_exclusion_risk"]:
            return "Iniquity exclusion triggered. Insurer may void coverage. Personal liability exposure creates urgency."
        elif gap > 5_000_000:
            return f"£{gap/1e6:.1f}m reserve gap. Insurer must escalate reserves or risk coverage stress."
        elif gap > 0:
            return f"£{gap/1e6:.1f}m reserve gap creates moderate pressure for settlement."
        else:
            return "Reserves adequate. Focus on liability merits rather than reserve pressure."
    
    def _generate_tactics(
        self,
        gap_analysis: dict,
        stress_analysis: dict,
    ) -> list[str]:
        """Generate tactical recommendations."""
        tactics = []
        
        if stress_analysis["iniquity_exclusion_risk"]:
            tactics.append("Emphasize personal liability exposure to Greeff/Jagusz if coverage voids")
            tactics.append("Request insurer confirm coverage position in writing")
            tactics.append("Consider approaching defendants directly, bypassing insurers")
        
        if gap_analysis["reserve_gap"] > 3_000_000:
            tactics.append("Highlight reserve inadequacy to claims handlers")
            tactics.append("Request reserve escalation to senior underwriters")
            tactics.append("Threaten full trial to force reserve increase")
        
        if not gap_analysis["within_policy_limit"]:
            tactics.append("Demand excess layer participation")
            tactics.append("Structure settlement within primary layer to avoid complexity")
        
        if not tactics:
            tactics.append("Standard negotiation approach - reserves not a pressure point")
            
        return tactics


def calculate_settlement_with_reserve_pressure(
    base_settlement_gbp: float,
    reserve_model: InsuranceReserveModel,
    active_flags: list[str],
) -> dict:
    """Calculate settlement range adjusted for reserve pressure.
    
    This function integrates with the settlement bands system to provide
    reserve-adjusted settlement ranges.
    
    Args:
        base_settlement_gbp: Base settlement from bands
        reserve_model: Configured reserve model
        active_flags: Active evidence flags
        
    Returns:
        Adjusted settlement analysis
    """
    report = reserve_model.generate_reserve_report(base_settlement_gbp, active_flags)
    leverage = report["negotiation_leverage"]["score"]
    
    # Apply leverage multiplier to settlement
    # Max 20% uplift for maximum leverage
    multiplier = 1.0 + (leverage / 10.0) * 0.2
    adjusted_settlement = base_settlement_gbp * multiplier
    
    return {
        "base_settlement": base_settlement_gbp,
        "reserve_adjusted_settlement": adjusted_settlement,
        "leverage_multiplier": multiplier,
        "reserve_report": report,
        "recommended_demand": min(adjusted_settlement, reserve_model.policy_limit),
    }
