"""Insurance Shadow Reserve - Dead money cost and reserve lockup model.

Illustrative reserve ratios for negotiation leverage calculation.
Court-safe language: "illustrative" not "actual insurer reserve".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional


@dataclass
class ShadowReserveAssumptions:
    """Explicit assumptions for shadow reserve model."""
    cost_of_capital_rate: float = 0.06  # 6% typical insurer cost of capital
    reserve_ratio_notification: float = 0.05
    reserve_ratio_defence_filed: float = 0.15
    reserve_ratio_procedural_irregularity: float = 0.35
    reserve_ratio_trial_listed: float = 0.65
    model_version: str = "insurance_shadow_v1.0"
    disclaimer: str = (
        "Illustrative reserve ratios for negotiation analysis. "
        "Not actual insurer-specific reserves."
    )


class InsuranceShadowReserve:
    """Shadow reserve model for locked capital estimation.
    
    Estimates capital locked in reserves and cost of "dead money".
    Uses illustrative ratios - not actual insurer data.
    """
    
    LITIGATION_STAGES = {
        "notification": {
            "reserve_ratio": 0.05,
            "description": "Claim notified, initial assessment",
        },
        "defence_filed": {
            "reserve_ratio": 0.15,
            "description": "Defence filed, liability contested",
        },
        "procedural_irregularity_flagged": {
            "reserve_ratio": 0.35,
            "description": "Procedural issues identified, exposure increased",
        },
        "trial_listed": {
            "reserve_ratio": 0.65,
            "description": "Trial listed, full reserve required",
        },
    }
    
    def __init__(self, assumptions: Optional[ShadowReserveAssumptions] = None):
        self.assumptions = assumptions or ShadowReserveAssumptions()
    
    def calculate_shadow_reserve(
        self,
        claim_value_gbp: float,
        litigation_stage: str,
        cost_of_capital_rate: Optional[float] = None,
    ) -> dict:
        """Calculate shadow reserve and dead money cost.
        
        Args:
            claim_value_gbp: Estimated claim value
            litigation_stage: One of LITIGATION_STAGES keys
            cost_of_capital_rate: Override default cost of capital
            
        Returns:
            Shadow reserve analysis with court-safe language
        """
        coc = cost_of_capital_rate if cost_of_capital_rate is not None else self.assumptions.cost_of_capital_rate
        
        # Get reserve ratio for stage
        stage_info = self.LITIGATION_STAGES.get(
            litigation_stage, 
            self.LITIGATION_STAGES["notification"]
        )
        reserve_ratio = stage_info["reserve_ratio"]
        
        # Calculate locked capital
        estimated_reserve_locked = claim_value_gbp * reserve_ratio
        
        # Calculate annual dead money cost
        annual_dead_money_cost = estimated_reserve_locked * coc
        
        # Generate negotiation lever insight
        negotiation_lever = self._generate_lever(
            litigation_stage, estimated_reserve_locked, annual_dead_money_cost
        )
        
        # Generate audit hash
        audit_data = {
            "claim_value": claim_value_gbp,
            "stage": litigation_stage,
            "reserve_ratio": reserve_ratio,
            "coc": coc,
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
                "claim_value_gbp": claim_value_gbp,
                "litigation_stage": litigation_stage,
                "cost_of_capital_rate": coc,
                "reserve_ratio_applied": reserve_ratio,
                "stage_description": stage_info["description"],
            },
            "shadow_reserve": {
                "estimated_reserve_locked_gbp": round(estimated_reserve_locked, 2),
                "reserve_ratio": reserve_ratio,
                "reserve_percentage": f"{reserve_ratio * 100:.0f}%",
            },
            "dead_money_cost": {
                "annual_cost_gbp": round(annual_dead_money_cost, 2),
                "monthly_cost_gbp": round(annual_dead_money_cost / 12, 2),
                "cost_of_capital_rate": f"{coc * 100:.1f}%",
            },
            "negotiation_lever": negotiation_lever,
            "illustrative_note": self.assumptions.disclaimer,
            "court_safe_summary": self._generate_summary(
                claim_value_gbp, litigation_stage, estimated_reserve_locked
            ),
        }
    
    def calculate_stage_progression(
        self,
        claim_value_gbp: float,
        current_stage: str,
        target_stage: str,
    ) -> dict:
        """Calculate reserve impact of stage progression.
        
        Args:
            claim_value_gbp: Estimated claim value
            current_stage: Current litigation stage
            target_stage: Target/hypothetical future stage
            
        Returns:
            Stage progression analysis
        """
        current = self.calculate_shadow_reserve(claim_value_gbp, current_stage)
        target = self.calculate_shadow_reserve(claim_value_gbp, target_stage)
        
        current_reserve = current["shadow_reserve"]["estimated_reserve_locked_gbp"]
        target_reserve = target["shadow_reserve"]["estimated_reserve_locked_gbp"]
        
        reserve_increase = target_reserve - current_reserve
        
        return {
            "current_stage": current_stage,
            "target_stage": target_stage,
            "current_reserve_gbp": current_reserve,
            "target_reserve_gbp": target_reserve,
            "reserve_increase_gbp": reserve_increase,
            "increase_percentage": (
                (reserve_increase / current_reserve * 100) if current_reserve > 0 else 0
            ),
            "negotiation_implication": (
                f"Progression to {target_stage} would increase locked capital by "
                f"£{reserve_increase:,.0f}"
            ),
        }
    
    def _generate_lever(
        self,
        stage: str,
        locked_capital: float,
        annual_cost: float,
    ) -> dict:
        """Generate negotiation lever insight."""
        if stage == "trial_listed":
            return {
                "lever_strength": "MAXIMUM",
                "rationale": (
                    f"Trial listed with £{locked_capital:,.0f} locked capital. "
                    f"Insurer paying £{annual_cost/12:,.0f}/month in dead money costs. "
                    "Strong incentive to settle before trial costs escalate."
                ),
                "suggested_tactic": (
                    "Emphasise trial cost escalation and certainty of judgment"
                ),
            }
        elif stage == "procedural_irregularity_flagged":
            return {
                "lever_strength": "HIGH",
                "rationale": (
                    f"Procedural issues flagged with £{locked_capital:,.0f} reserved. "
                    "Reserve escalation creates pressure for early resolution."
                ),
                "suggested_tactic": (
                    "Highlight reserve inadequacy and need for escalation"
                ),
            }
        elif stage == "defence_filed":
            return {
                "lever_strength": "MODERATE",
                "rationale": (
                    f"Active litigation with £{locked_capital:,.0f} reserved. "
                    "Moderate pressure as case develops."
                ),
                "suggested_tactic": (
                    "Build leverage through evidence development"
                ),
            }
        else:
            return {
                "lever_strength": "LOW",
                "rationale": (
                    f"Early stage with £{locked_capital:,.0f} provisionally reserved. "
                    "Limited reserve pressure at this stage."
                ),
                "suggested_tactic": (
                    "Focus on liability merits rather than reserve pressure"
                ),
            }
    
    def _generate_summary(
        self,
        claim_value: float,
        stage: str,
        locked: float,
    ) -> str:
        """Generate court-safe summary."""
        stage_desc = self.LITIGATION_STAGES.get(stage, {}).get(
            "description", "Litigation in progress"
        )
        
        return (
            f"At the {stage.replace('_', ' ')} stage, illustrative analysis suggests "
            f"£{locked:,.0f} in reserve capital may be allocated. "
            f"This represents a negotiation consideration, not an actual insurer reserve."
        )


def quick_shadow_check(
    claim_value_gbp: float = 5_000_000,
    litigation_stage: str = "procedural_irregularity_flagged",
) -> dict:
    """Quick shadow reserve check without full initialization."""
    shadow = InsuranceShadowReserve()
    return shadow.calculate_shadow_reserve(claim_value_gbp, litigation_stage)
