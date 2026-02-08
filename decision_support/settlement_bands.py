"""Settlement Bands - Three explicit bands for defensible pricing.

BASE: Present-day, evidence-only value
VALIDATION: Value after one external validation event  
TAIL: Value after multiple compounding validation events

No mixing of leverage with valuation. No inflation of BASE with future risks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


SettlementBand = Literal["BASE", "VALIDATION", "TAIL"]


@dataclass
class BandConfiguration:
    """Configuration for a settlement band."""
    name: str
    minimum_gbp: float
    maximum_gbp: float
    description: str
    meaning: str
    activation_flags: list[str]
    required_flag_count: int


# Three explicit settlement bands (event-driven, not speculative)
BAND_DEFINITIONS: dict[SettlementBand, BandConfiguration] = {
    "BASE": BandConfiguration(
        name="Base Settlement Band",
        minimum_gbp=2_500_000,
        maximum_gbp=4_000_000,
        description="Current, evidence-only value",
        meaning="What a rational insurer can authorise TODAY",
        activation_flags=[],  # Default - no triggers required
        required_flag_count=0
    ),
    "VALIDATION": BandConfiguration(
        name="Validation Settlement Band",
        minimum_gbp=5_000_000,
        maximum_gbp=9_000_000,
        description="Price after ONE external validation event",
        meaning="Value after external authority confirms procedural irregularity",
        activation_flags=[
            "judicial_comment_on_record",
            "sra_investigation_open",
            "insurer_expanded_reservation",
            "court_directed_explanation"
        ],
        required_flag_count=1  # Any ONE of the above
    ),
    "TAIL": BandConfiguration(
        name="Tail Risk Settlement Band",
        minimum_gbp=12_000_000,
        maximum_gbp=15_000_000,
        description="Existential containment pricing",
        meaning="Catastrophic prevention pricing - not 'likely' outcome",
        activation_flags=[
            "adverse_judicial_language",
            "sra_formal_action",
            "insurance_coverage_stress",
            "part_26a_disclosure_conflict",
            "criminal_investigation_escalation"
        ],
        required_flag_count=2  # TWO OR MORE required
    )
}


class SettlementBandCalculator:
    """Deterministic band calculator - binary logic only, no weighting."""
    
    def __init__(self, active_flags: list[str]):
        self.active_flags = set(active_flags)
        self.current_band = self._determine_band()
        self.inactive_bands = self._get_inactive_bands()
    
    def _determine_band(self) -> SettlementBand:
        """Determine current band based on active flags.
        
        Rules:
        - 0 triggering flags → BASE
        - 1 validation flag → VALIDATION  
        - ≥2 tail flags → TAIL
        """
        tail_flags = set(BAND_DEFINITIONS["TAIL"].activation_flags)
        validation_flags = set(BAND_DEFINITIONS["VALIDATION"].activation_flags)
        
        # Count flags in each category
        active_tail = len(self.active_flags & tail_flags)
        active_validation = len(self.active_flags & validation_flags)
        
        # Binary logic - no weighting
        if active_tail >= 2:
            return "TAIL"
        elif active_validation >= 1:
            return "VALIDATION"
        else:
            return "BASE"
    
    def _get_inactive_bands(self) -> list[SettlementBand]:
        """Get list of bands not currently active."""
        all_bands: list[SettlementBand] = ["BASE", "VALIDATION", "TAIL"]
        return [b for b in all_bands if b != self.current_band]
    
    def get_band_config(self) -> BandConfiguration:
        """Get configuration for current band."""
        return BAND_DEFINITIONS[self.current_band]
    
    def get_what_moves_up(self) -> dict:
        """Generate 'What moves this up a band?' explanation.
        
        Returns:
            Dictionary with next band and missing flags
        """
        if self.current_band == "BASE":
            next_band = "VALIDATION"
            missing = list(set(BAND_DEFINITIONS["VALIDATION"].activation_flags) - self.active_flags)
            return {
                "next_band": next_band,
                "next_range": "£5.0m–£9.0m",
                "flags_needed": 1,
                "missing_flags": missing,
                "message": f"Activate VALIDATION band with any ONE of: {', '.join(missing[:3])}..."
            }
        elif self.current_band == "VALIDATION":
            next_band = "TAIL"
            tail_flags = set(BAND_DEFINITIONS["TAIL"].activation_flags)
            active_tail = len(self.active_flags & tail_flags)
            missing_tail = list(tail_flags - self.active_flags)
            flags_needed = max(0, 2 - active_tail)
            
            return {
                "next_band": next_band,
                "next_range": "£12.0m–£15.0m",
                "flags_needed": flags_needed,
                "missing_flags": missing_tail,
                "message": f"Activate TAIL band with {flags_needed} more tail flag(s): {', '.join(missing_tail[:3])}..."
            }
        else:
            return {
                "next_band": None,
                "next_range": None,
                "flags_needed": 0,
                "missing_flags": [],
                "message": "Already at TAIL band - maximum escalation reached"
            }
    
    def generate_band_summary(self) -> dict:
        """Generate comprehensive band summary for dashboard."""
        current = self.get_band_config()
        what_moves = self.get_what_moves_up()
        
        return {
            "current_band": self.current_band,
            "current_band_name": current.name,
            "current_range": f"£{current.minimum_gbp/1e6:.1f}m–£{current.maximum_gbp/1e6:.1f}m",
            "minimum_gbp": current.minimum_gbp,
            "maximum_gbp": current.maximum_gbp,
            "meaning": current.meaning,
            "description": current.description,
            "active_flags": list(self.active_flags),
            "inactive_bands": self.inactive_bands,
            "what_moves_up": what_moves,
        }


def generate_settlement_letter_banded(
    band_calculator: SettlementBandCalculator,
    claimant_name: str,
    respondent_name: str,
    case_reference: str,
    principal_claim: float,
) -> str:
    """Generate settlement letter using banded framing.
    
    Uses court-safe language. £15m appears only as TAIL band.
    """
    band = band_calculator.get_band_config()
    summary = band_calculator.generate_band_summary()
    what_moves = band_calculator.get_what_moves_up()
    
    letter = f"""WITHOUT PREJUDICE SAVE AS TO COSTS

Settlement Proposal - {case_reference}

Dear Sirs,

Re: {claimant_name} v {respondent_name}

We write to set out our client's position regarding settlement of the above matter.

CURRENT SETTLEMENT BAND: {band.name}

Based on the procedural posture and disclosed facts, this matter currently sits in the 
**{band.name}** ({summary['current_range']}).

Band Meaning:
{band.meaning}

Settlement Range: £{band.minimum_gbp:,.0f} – £{band.maximum_gbp:,.0f}

ACTIVE FLAGS

{chr(10).join(f"  • {flag.replace('_', ' ').title()}" for flag in summary['active_flags']) if summary['active_flags'] else '  • None - Base position applies'}

WHAT MOVES THIS UP A BAND?

{what_moves['message']}

{f"Next Band: {what_moves['next_band']} ({what_moves['next_range']})" if what_moves['next_band'] else "This is the maximum escalation band."}

Our client's settlement expectation reflects the current band position. Any material 
change in the flag profile would trigger reassessment at the next band level.

We are instructed to seek £{band.maximum_gbp:,.0f} in full and final settlement.

This offer remains open for 14 days from the date of this letter.

Yours faithfully,

[Claimant's Solicitors]

---

Band Methodology Note:
This settlement framework uses three explicit bands based on external validation events:

• BASE (£2.5m–£4.0m): Present-day, evidence-only value
• VALIDATION (£5.0m–£9.0m): After one external validation event
• TAIL (£12.0m–£15.0m): Existential containment pricing (catastrophic prevention)

Each band requires specific triggering events. The current band reflects only 
confirmed flags, not speculative risks.
"""
    
    return letter


def get_what_moves_up_explanation(calculator: SettlementBandCalculator) -> str:
    """Generate 'What Moves This Up a Band?' panel content."""
    current = calculator.get_band_config()
    what_moves = calculator.get_what_moves_up()
    
    lines = [
        f"## What Moves This From {current.name} to {what_moves['next_band'] or 'Higher'}?",
        "",
        f"**Current Position:** {current.name}",
        f"• Range: £{current.minimum_gbp/1e6:.1f}m–£{current.maximum_gbp/1e6:.1f}m",
        f"• Meaning: {current.meaning}",
        f"• Active Flags: {len(calculator.active_flags)}",
        "",
    ]
    
    if what_moves['next_band']:
        next_config = BAND_DEFINITIONS[what_moves['next_band']]
        lines.extend([
            f"**Next Band:** {next_config.name}",
            f"• Range: £{next_config.minimum_gbp/1e6:.1f}m–£{next_config.maximum_gbp/1e6:.1f}m",
            f"• Flags Required: {what_moves['flags_needed']}",
            f"• Range Increase: +£{(next_config.minimum_gbp - current.maximum_gbp)/1e6:.1f}m minimum",
            "",
            "**Missing Flags (Any of these would trigger):**",
        ])
        for flag in what_moves['missing_flags'][:5]:
            lines.append(f"  ☐ {flag.replace('_', ' ').title()}")
    else:
        lines.extend([
            "**Status:** Maximum band achieved",
            "No higher band exists in this framework.",
        ])
    
    lines.extend([
        "",
        "---",
        "",
        "**Band Logic Summary:**",
        "• BASE (0 flags): Current, evidence-only value",
        "• VALIDATION (1 flag): After external authority validation",
        "• TAIL (≥2 flags): Catastrophic prevention pricing",
        "",
        "**Important:** £15m is TAIL band only - existential containment, not current valuation.",
    ])
    
    return "\n".join(lines)
