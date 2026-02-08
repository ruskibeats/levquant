"""Banded Settlement Framework - Flag-driven band activation.

Converts binary flags into graduated settlement bands with clear escalation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


SettlementBand = Literal["BASE", "BAND_1", "BAND_2", "BAND_3", "MAXIMUM"]


@dataclass
class BandConfiguration:
    """Configuration for a settlement band."""
    name: str
    minimum_gbp: float
    typical_gbp: float
    description: str
    activation_flags: list[str]
    required_flag_count: int
    unlock_message: str


# Band definitions with flag activation requirements
# Updated based on forensic valuation (HMCTS SAR, Sally email, Maven DSAR, Police Report)
BAND_DEFINITIONS: dict[SettlementBand, BandConfiguration] = {
    "BASE": BandConfiguration(
        name="Base Settlement Range",
        minimum_gbp=66_000,
        typical_gbp=500_000,
        description="Debt recovery without aggravating factors",
        activation_flags=[],
        required_flag_count=0,
        unlock_message="Default position - no special flags required"
    ),
    "BAND_1": BandConfiguration(
        name="Elevated Risk Band",
        minimum_gbp=1_500_000,
        typical_gbp=3_000_000,
        description="Material procedural irregularities - £3m now the discount floor",
        activation_flags=[
            "defence_nullity_confirmed",
            "hmcts_sar_no_10june",
            "metadata_12june_creation"
        ],
        required_flag_count=2,
        unlock_message="Activate with: HMCTS SAR (no 10 June) + Metadata proving 12 June creation"
    ),
    "BAND_2": BandConfiguration(
        name="Serious Misconduct Band",
        minimum_gbp=3_000_000,
        typical_gbp=7_000_000,
        description="Containment pricing - selling survival not debt",
        activation_flags=[
            "defence_nullity_confirmed",
            "hmcts_sar_no_10june",
            "metadata_12june_creation",
            "sally_email_4june",
            "maven_dsar_refusal",
            "police_report_crn_418493325"
        ],
        required_flag_count=4,
        unlock_message="Activate with: 4+ evidence sources (Sally email, DSAR refusal, Police Report)"
    ),
    "BAND_3": BandConfiguration(
        name="Critical Exposure Band",
        minimum_gbp=5_000_000,
        typical_gbp=9_000_000,
        description="Existential risk - SRA/FCA/SDT exposure confirmed",
        activation_flags=[
            "defence_nullity_confirmed",
            "hmcts_sar_no_10june",
            "metadata_12june_creation",
            "sally_email_4june",
            "maven_dsar_refusal",
            "police_report_crn_418493325",
            "sra_principles_1_2_breach"
        ],
        required_flag_count=6,
        unlock_message="Activate with: 6+ flags including SRA breach or FCA SMCR exposure"
    ),
    "MAXIMUM": BandConfiguration(
        name="Maximum Containment Band",
        minimum_gbp=9_000_000,
        typical_gbp=15_000_000,
        description="Total containment failure - shadow director proven",
        activation_flags=[
            "defence_nullity_confirmed",
            "hmcts_sar_no_10june",
            "metadata_12june_creation",
            "sally_email_4june",
            "maven_dsar_refusal",
            "police_report_crn_418493325",
            "sra_principles_1_2_breach",
            "shadow_director_sanjay_patel",
            "part_26a_restructuring_risk"
        ],
        required_flag_count=8,
        unlock_message="Activate with: 8+ flags including Shadow Director proven + Part 26A collapse risk"
    )
}


# Forensic evidence sources for calibration
FORENSIC_EVIDENCE_SOURCES = {
    "hmcts_sar_no_10june": {
        "name": "HMCTS SAR Logs",
        "source": "251104064 R Batchelor SAR data.pdf",
        "proves": "Zero activity on 10 June - '10 June receipt' is administrative fiction",
        "risk": "Defence nullity proven"
    },
    "metadata_12june_creation": {
        "name": "Forensic Metadata Analysis",
        "source": "Forensic Analysis",
        "proves": "Defence created 12 June, not 10 June",
        "risk": "Timeline fraud established"
    },
    "sally_email_4june": {
        "name": "Freeths 'Sally' Email",
        "source": "inside dealing copy.pdf",
        "proves": "Seven solicitors knowingly advanced false timeline",
        "risk": "SRA Principles 1 & 2 (Integrity/Rule of Law) - strike-off risk"
    },
    "maven_dsar_refusal": {
        "name": "Maven DSAR Refusal",
        "source": "RBatchelor 20260112 (1).pdf",
        "proves": "Sanjay Patel shadow director orchestrating litigation",
        "risk": "FCA/SMCR failure to act with integrity (COCON 2.1.1)"
    },
    "police_report_crn_418493325": {
        "name": "Police Report",
        "source": "FormSubmission...ir04.pdf",
        "proves": "Suspect 1 (Greeff) forgery + liberty risk",
        "risk": "Criminal charges + director disqualification"
    },
    "part_26a_restructuring_risk": {
        "name": "Part 26A Restructuring",
        "source": "Chancery Division pending",
        "proves": "Flow UK lying to High Court about debt validity",
        "risk": "Restructuring collapses if SAR logs filed"
    }
}


class ForensicValuationEngine:
    """Forensic valuation based on evidence bundle."""
    
    @staticmethod
    def calculate_containment_value(
        base_debt: float,
        active_evidence: list[str],
        regulatory_triggers: list[str]
    ) -> dict:
        """Calculate containment value based on forensic evidence.
        
        Args:
            base_debt: Original debt amount (£66k)
            active_evidence: List of active evidence sources
            regulatory_triggers: List of SRA/FCA/Police triggers activated
        
        Returns:
            Valuation dictionary
        """
        # Base is no longer the debt - it's the containment floor
        containment_floor = 3_000_000  # £3m is now the floor, not ceiling
        
        # Multipliers based on regulatory exposure
        multipliers = {
            "sra_investigation": 1.5,      # SRA looking at firm
            "fca_smcr_breach": 2.0,        # FCA regulated person involved
            "police_criminal": 2.5,        # Criminal charges pending
            "shadow_director_proven": 3.0,  # Sanjay Patel proven as controller
            "part_26a_collapse": 2.0       # Restructuring at risk
        }
        
        total_multiplier = 1.0
        for trigger in regulatory_triggers:
            if trigger in multipliers:
                total_multiplier *= multipliers[trigger]
        
        # Cap multiplier at reasonable level
        total_multiplier = min(total_multiplier, 5.0)
        
        valuation = containment_floor * total_multiplier
        
        return {
            "base_debt": base_debt,
            "containment_floor": containment_floor,
            "regulatory_multiplier": total_multiplier,
            "forensic_valuation": valuation,
            "active_evidence": active_evidence,
            "regulatory_triggers": regulatory_triggers,
            "valuation_rationale": f"£3m containment floor × {total_multiplier:.1f} regulatory exposure"
        }

    @staticmethod
    def get_strategic_recommendation(evidence_count: int) -> str:
        """Get strategic recommendation based on evidence strength."""
        if evidence_count >= 6:
            return """
STRATEGIC RECOMMENDATION (Maximum Leverage):

1. SERVE DRAFT HIGH COURT EVIDENCE: Send draft Witness Statement for Part 26A 
   hearing to Freeths. Exhibit HMCTS SAR Log (No 10 June entry) + Metadata.
   State: "I am duty-bound to put this before the Chancery Judge."

2. DATA CONTROLLER PINCER: Write to Chris Jagusz and Claire Speirs personally.
   Tell them Freeths identified them as Respondents - they are personally liable.
   Threaten court order to inspect "Shadow Servers."

3. THE OFFER: "£3m was the price for the debt. The price for resolving the 
   regulatory and criminal exposure is significantly higher. My settlement 
   floor is now £6.5m+"

RATIONAL SETTLEMENT RANGE: £5m - £9m
"""
        elif evidence_count >= 4:
            return """
STRATEGIC RECOMMENDATION (Strong Leverage):

You hold nuclear material. Serve the evidence bundle to insurers and regulators.
Settlement floor: £3m (containment) not £66k (debt).

Target: £5m - £7m
"""
        else:
            return """
STRATEGIC RECOMMENDATION (Building Leverage):

Continue evidence collection. Current position: Elevated Risk Band.
Settlement floor: £1.5m

Target: £2m - £3m
"""


class SettlementBandCalculator:
    """Calculates settlement bands based on active flags."""
    
    def __init__(self, active_flags: list[str]):
        self.active_flags = set(active_flags)
        self.current_band = self._calculate_band()
        self.next_band = self._calculate_next_band()
    
    def _calculate_band(self) -> SettlementBand:
        """Determine current settlement band based on active flags."""
        flag_count = len(self.active_flags)
        
        # Check bands in reverse order (highest first)
        if flag_count >= 5:
            return "MAXIMUM"
        elif flag_count >= 4:
            return "BAND_3"
        elif flag_count >= 3:
            return "BAND_2"
        elif flag_count >= 1:
            return "BAND_1"
        else:
            return "BASE"
    
    def _calculate_next_band(self) -> Optional[SettlementBand]:
        """Calculate what band we could reach with one more flag."""
        band_order: list[SettlementBand] = ["BASE", "BAND_1", "BAND_2", "BAND_3", "MAXIMUM"]
        
        try:
            current_idx = band_order.index(self.current_band)
            if current_idx < len(band_order) - 1:
                return band_order[current_idx + 1]
        except ValueError:
            pass
        
        return None
    
    def get_band_config(self) -> BandConfiguration:
        """Get configuration for current band."""
        return BAND_DEFINITIONS[self.current_band]
    
    def get_next_band_config(self) -> Optional[BandConfiguration]:
        """Get configuration for next achievable band."""
        if self.next_band:
            return BAND_DEFINITIONS[self.next_band]
        return None
    
    def flags_needed_for_next_band(self) -> dict:
        """Calculate what's needed to reach next band."""
        if not self.next_band:
            return {
                "next_band": None,
                "flags_needed": 0,
                "missing_flags": [],
                "message": "Already at maximum band"
            }
        
        next_config = BAND_DEFINITIONS[self.next_band]
        current_count = len(self.active_flags)
        target_count = next_config.required_flag_count
        flags_needed = target_count - current_count
        
        # Find which flags would activate next band
        relevant_flags = set(next_config.activation_flags)
        missing_flags = relevant_flags - self.active_flags
        
        return {
            "next_band": self.next_band,
            "flags_needed": max(0, flags_needed),
            "missing_flags": list(missing_flags),
            "message": f"Need {flags_needed} more flag(s) from: {', '.join(missing_flags)}"
        }
    
    def generate_band_summary(self) -> dict:
        """Generate comprehensive band summary for dashboard."""
        current = self.get_band_config()
        next_info = self.flags_needed_for_next_band()
        
        return {
            "current_band": self.current_band,
            "current_band_name": current.name,
            "minimum_settlement": current.minimum_gbp,
            "typical_settlement": current.typical_gbp,
            "description": current.description,
            "active_flags": list(self.active_flags),
            "flag_count": len(self.active_flags),
            "next_band": next_info["next_band"],
            "flags_needed_for_next": next_info["flags_needed"],
            "what_moves_up": next_info["message"],
            "unlock_requirements": current.unlock_message
        }


def generate_settlement_letter_banded(
    band_calculator: SettlementBandCalculator,
    claimant_name: str,
    respondent_name: str,
    case_reference: str,
    principal_claim: float,
) -> str:
    """Generate settlement letter using banded framing.
    
    Args:
        band_calculator: Configured band calculator
        claimant_name: Name of claimant
        respondent_name: Name of respondent
        case_reference: Case reference number
        principal_claim: Principal claim amount
    
    Returns:
        Formatted settlement letter text
    """
    band = band_calculator.get_band_config()
    summary = band_calculator.generate_band_summary()
    
    letter = f"""WITHOUT PREJUDICE SAVE AS TO COSTS

Settlement Proposal - {case_reference}

Dear Sirs,

Re: {claimant_name} v {respondent_name}

We write to set out our client's position regarding settlement of the above matter.

CURRENT SETTLEMENT BAND: {band.name}

Based on the procedural posture and disclosed facts, this matter currently sits in the 
**{band.name}** with the following characteristics:

• Minimum Settlement Expectation: £{band.minimum_gbp:,.0f}
• Typical Settlement Range: £{band.typical_gbp:,.0f}
• Risk Profile: {band.description}

FLAG ANALYSIS

Active Flags ({summary['flag_count']}):
{chr(10).join(f"  • {flag.replace('_', ' ').title()}" for flag in summary['active_flags']) if summary['active_flags'] else '  • None - Base position applies'}

{band.unlock_message}

WHAT MOVES US UP A BAND?

{summary['what_moves_up']}

Our client's settlement expectation reflects the current band position. Any material 
change in the flag profile (e.g., {band_calculator.flags_needed_for_next_band()['missing_flags'][0] if band_calculator.flags_needed_for_next_band()['missing_flags'] else 'additional developments'}) would trigger 
reassessment at the next band level.

We are instructed to seek £{band.typical_gbp:,.0f} in full and final settlement, 
reflecting:

• Principal claim: £{principal_claim:,.0f}
• Procedural leverage premium (current band): £{band.typical_gbp - principal_claim:,.0f}
• Total: £{band.typical_gbp:,.0f}

This offer remains open for 14 days from the date of this letter.

Yours faithfully,

[Claimant's Solicitors]

---

Band Methodology Note:
This settlement framework uses a graduated band system based on objective procedural 
and factual flags. Each band activation requires specific verified triggers. The 
current band reflects only those flags that have been confirmed through evidence.
"""
    
    return letter


def get_what_moves_up_explanation(calculator: SettlementBandCalculator) -> str:
    """Generate plain English explanation of what moves to next band.
    
    Args:
        calculator: Settlement band calculator
    
    Returns:
        Formatted explanation text
    """
    current = calculator.get_band_config()
    next_band = calculator.get_next_band_config()
    needed = calculator.flags_needed_for_next_band()
    
    lines = [
        f"## What Moves Us From {current.name} to {next_band.name if next_band else 'Higher'}?",
        "",
        f"**Current Position:** {current.name}",
        f"• Active Flags: {len(calculator.active_flags)}",
        f"• Settlement Floor: £{current.minimum_gbp:,.0f}",
        "",
    ]
    
    if next_band:
        lines.extend([
            f"**Next Band:** {next_band.name}",
            f"• Required Flags: {next_band.required_flag_count}",
            f"• Settlement Floor: £{next_band.minimum_gbp:,.0f}",
            f"• Difference: +£{next_band.minimum_gbp - current.minimum_gbp:,.0f}",
            "",
            "**What Triggers the Move:**",
            f"{needed['message']}",
            "",
            "**Missing Flags:**",
        ])
        for flag in needed['missing_flags'][:3]:  # Show top 3
            lines.append(f"  ☐ {flag.replace('_', ' ').title()}")
    else:
        lines.extend([
            "**Status:** Maximum band achieved",
            "All 5 flags are active. No higher band exists in this framework.",
        ])
    
    lines.extend([
        "",
        "---",
        "",
        "**Band Logic:**",
        "• BASE (0 flags): Standard dispute resolution",
        "• BAND 1 (1+ flags): Material irregularities present",
        "• BAND 2 (3+ flags): Confirmed misconduct with exposure",
        "• BAND 3 (4+ flags): Partner-level existential risk",
        "• MAXIMUM (5 flags): Catastrophic public exposure imminent",
    ])
    
    return "\n".join(lines)
