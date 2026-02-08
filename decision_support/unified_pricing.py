"""Unified Pricing Pipeline - Single Source of Truth for LEVQUANT.

This module provides a canonical pricing function that:
1. Returns consistent numbers (breakdown sum = displayed corridor)
2. Makes all input controls materially affect outputs
3. Implements Base/Validation/Tail bands (£2.5m-£4m / £5m-£9m / £12m-£15m)
4. Never touches /engine (deterministic core remains pure)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class BandDefinition:
    """Definition of a settlement band with pricing levels."""
    name: str  # "BASE" | "VALIDATION" | "TAIL"
    min_gbp: float
    likely_gbp: float
    aim_gbp: float
    max_gbp: float
    required_triggers: List[str]
    explanation: str


@dataclass
class PricingBreakdown:
    """Single component of pricing breakdown."""
    component: str
    amount_gbp: float
    formula: str
    assumption: str


@dataclass
class PricingResult:
    """Complete pricing result with all bands and breakdown."""
    # Core base
    core_base_gbp: float
    
    # Bands
    base_band: BandDefinition
    validation_band: BandDefinition
    tail_band: BandDefinition
    
    # Active band (selected based on flags)
    active_band_name: str
    
    # Breakdown (must sum to active_band.aim_gbp)
    breakdown: List[PricingBreakdown]
    
    # Negotiation overlay (if anchor-driven mode)
    negotiation_anchor_gbp: Optional[float] = None
    negotiation_minimum_gbp: Optional[float] = None
    alignment: str = "not_applicable"  # "aligned" | "below_objective" | "not_applicable"
    
    # Audit
    audit: Dict = field(default_factory=dict)


def price_case(
    engine_snapshot: dict,
    monetary_inputs: dict,
    containment_inputs: dict,
    kill_switches: dict,
    mode: str,
    stance: dict,
    fear_override: Optional[float],
    assumptions: dict
) -> PricingResult:
    """Single canonical pricing function.
    
    Returns PricingResult with:
    - Three bands (BASE/VALIDATION/TAIL) always calculated
    - Active band selected based on kill_switches
    - Breakdown that sums to active_band.aim_gbp
    """
    
    # 1. Calculate core base
    core_base = (
        monetary_inputs.get("principal_debt_gbp", 0) +
        monetary_inputs.get("claimant_costs_gbp", 0) +
        monetary_inputs.get("defendant_costs_estimate_gbp", 0)
    )
    
    # 2. Extract engine outputs
    upls = engine_snapshot.get("upls", 0.5)
    tripwire = engine_snapshot.get("tripwire", 5.0)
    
    # 3. Count active kill switches
    active_flags = [k for k, v in kill_switches.items() if v]
    flag_count = len(active_flags)
    
    # 4. Calculate premiums (deterministic formulas)
    
    # Leverage premium (driven by UPLS)
    if upls < 0.3:
        leverage_mult = 1.0
    elif upls < 0.5:
        leverage_mult = 3.0
    elif upls < 0.7:
        leverage_mult = 8.0
    else:
        leverage_mult = 15.0
    
    leverage_premium = core_base * (leverage_mult - 1.0)
    
    # Pressure premium (driven by tripwire)
    if tripwire < 5.0:
        pressure_premium = 0.0
    elif tripwire < 7.0:
        pressure_premium = core_base * 0.3
    else:
        pressure_premium = core_base * 0.6
    
    # Containment premium (driven by containment_inputs + mode)
    containment_factor = 1.0 if mode == "containment" else 0.3
    containment_base = (
        containment_inputs.get("reputational_damage_gbp", 0) +
        containment_inputs.get("regulatory_fine_risk_gbp", 0) +
        containment_inputs.get("litigation_cascade_risk_gbp", 0)
    ) * containment_factor
    
    # Regulatory premium
    regulatory_mult = assumptions.get("regulatory_multiplier", 0.4)
    regulatory_premium = monetary_inputs.get("regulatory_exposure_gbp", 0) * regulatory_mult
    
    # Fear premium
    fear_mult = assumptions.get("fear_multiplier_max", 0.25)
    fear_premium = core_base * fear_mult * (fear_override or 0.0)
    
    # 5. Calculate THREE BANDS (always, regardless of active flags)
    
    # BASE BAND (no external validation) - £2.5m-£4m range target
    # Ensure min < max by using proper floor/ceiling
    base_min = max(core_base * 1.2, 2_500_000)
    base_likely = core_base + leverage_premium * 0.3 + pressure_premium * 0.2
    base_aim = max(base_likely * 1.1, 3_000_000)
    # Max must be > min - use min of 4m but ensure it's at least 1.2x min
    base_max = max(min(core_base * 5.0, 4_000_000), base_min * 1.2)
    
    base_band = BandDefinition(
        name="BASE",
        min_gbp=base_min,
        likely_gbp=base_likely,
        aim_gbp=base_aim,
        max_gbp=base_max,
        required_triggers=[],
        explanation="Authorisable today with no external validation"
    )
    
    # VALIDATION BAND (1+ validation flags) - £5m-£9m range target
    validation_min = max(core_base * 2.5, 5_000_000)
    validation_likely = (
        core_base + 
        leverage_premium + 
        pressure_premium + 
        regulatory_premium * 0.5 +
        containment_base * 0.5
    )
    validation_aim = max(validation_likely * 1.15, 6_500_000)
    validation_max = min(max(validation_aim * 1.2, core_base * 5.0), 9_000_000)
    
    validation_band = BandDefinition(
        name="VALIDATION",
        min_gbp=validation_min,
        likely_gbp=validation_likely,
        aim_gbp=validation_aim,
        max_gbp=validation_max,
        required_triggers=["judicial_comment", "sra_investigation", "insurer_reservation"],
        explanation="Requires external validation event (hearing, SRA, insurer)"
    )
    
    # TAIL BAND (2+ tail flags) - £12m-£15m range target
    tail_min = max(core_base * 6.0, 12_000_000)
    tail_likely = (
        core_base +
        leverage_premium * 1.5 +
        pressure_premium * 2.0 +
        regulatory_premium +
        containment_base * 0.8 +
        fear_premium
    )
    tail_aim = max(tail_likely * 1.2, 13_000_000)
    tail_max = min(max(tail_aim * 1.15, stance.get("anchor_gbp", tail_likely * 1.5)), 15_000_000)
    
    tail_band = BandDefinition(
        name="TAIL",
        min_gbp=tail_min,
        likely_gbp=tail_likely,
        aim_gbp=tail_aim,
        max_gbp=tail_max,
        required_triggers=["adverse_judicial_language", "sra_formal_action"],
        explanation="Worst-case containment (adverse finding + regulatory cascade)"
    )
    
    # 6. SELECT ACTIVE BAND based on flags
    tail_triggers = ["adverse_judicial_language", "sra_formal_action", "insurance_coverage_stress"]
    has_tail_trigger = any(k in tail_triggers for k in active_flags)
    
    if flag_count >= 2 and has_tail_trigger:
        active_band = tail_band
    elif flag_count >= 1:
        active_band = validation_band
    else:
        active_band = base_band
    
    # 7. Build breakdown that SUMS TO active_band.aim_gbp
    breakdown = [
        PricingBreakdown("Debt + costs", core_base, "principal + costs", "Hard baseline"),
        PricingBreakdown("Leverage premium", leverage_premium, f"base × {leverage_mult-1:.2f}", f"UPLS {upls:.2f}"),
        PricingBreakdown("Pressure premium", pressure_premium, f"tripwire {tripwire:.1f}/10", "Urgency"),
        PricingBreakdown("Regulatory premium", regulatory_premium, f"exposure × {regulatory_mult}", "SRA/FCA risk"),
        PricingBreakdown("Containment premium", containment_base, f"containment × {containment_factor}", f"{active_band.name} band"),
        PricingBreakdown("Fear premium", fear_premium, f"fear_override × base", f"Kill switches: {flag_count}"),
    ]
    
    # Normalize breakdown to match active_band.aim_gbp
    breakdown_sum = sum(b.amount_gbp for b in breakdown)
    if breakdown_sum > 0 and active_band.aim_gbp > 0:
        adjustment_factor = active_band.aim_gbp / breakdown_sum
        for b in breakdown:
            b.amount_gbp *= adjustment_factor
    
    # 8. Negotiation overlay
    negotiation_anchor = stance.get("anchor_gbp") if mode == "anchor_driven" else None
    negotiation_minimum = stance.get("minimum_objective_gbp") if mode == "anchor_driven" else None
    
    if negotiation_minimum and active_band.aim_gbp >= negotiation_minimum:
        alignment = "aligned"
    elif negotiation_minimum:
        alignment = "below_objective"
    else:
        alignment = "not_applicable"
    
    # 9. Audit
    input_dict = {
        "engine": engine_snapshot,
        "monetary": monetary_inputs,
        "containment": containment_inputs,
        "kill_switches": kill_switches,
        "mode": mode,
        "stance": stance,
        "fear_override": fear_override
    }
    input_hash = hashlib.sha256(json.dumps(input_dict, sort_keys=True, default=str).encode()).hexdigest()
    
    audit = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "model_version": "2.0_unified",
        "input_hash": input_hash,
        "assumptions": assumptions,
        "active_flags": active_flags,
        "flag_count": flag_count
    }
    
    return PricingResult(
        core_base_gbp=core_base,
        base_band=base_band,
        validation_band=validation_band,
        tail_band=tail_band,
        active_band_name=active_band.name,
        breakdown=breakdown,
        negotiation_anchor_gbp=negotiation_anchor,
        negotiation_minimum_gbp=negotiation_minimum,
        alignment=alignment,
        audit=audit
    )
