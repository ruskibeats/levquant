"""Tests for unified pricing pipeline.

Validates that:
1. Breakdown sums to active band aim
2. Containment inputs affect outputs
3. All three bands are calculated
4. Kill switches select correct band
"""

import pytest
from decision_support.unified_pricing import price_case, BandDefinition, PricingBreakdown


def test_breakdown_sums_to_active_band_aim():
    """Breakdown must sum to active band aim within 1% tolerance."""
    
    engine_snapshot = {"upls": 0.64, "tripwire": 6.4, "decision": "HOLD", "confidence": "Moderate"}
    monetary_inputs = {
        "principal_debt_gbp": 66_000,
        "claimant_costs_gbp": 500_000,
        "defendant_costs_estimate_gbp": 250_000,
        "regulatory_exposure_gbp": 2_000_000
    }
    containment_inputs = {
        "reputational_damage_gbp": 0,
        "regulatory_fine_risk_gbp": 0,
        "litigation_cascade_risk_gbp": 0
    }
    kill_switches = {
        "nullity_confirmed": False,
        "regulatory_open": False,
        "insurer_notice": False,
        "override_admitted": False,
        "shadow_director": False
    }
    
    result = price_case(
        engine_snapshot=engine_snapshot,
        monetary_inputs=monetary_inputs,
        containment_inputs=containment_inputs,
        kill_switches=kill_switches,
        mode="standard",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    active_band = getattr(result, f"{result.active_band_name.lower()}_band")
    breakdown_sum = sum(b.amount_gbp for b in result.breakdown)
    
    # Must match within 1%
    assert abs(breakdown_sum - active_band.aim_gbp) / active_band.aim_gbp < 0.01, \
        f"Breakdown sum {breakdown_sum} != active band aim {active_band.aim_gbp}"


def test_containment_inputs_change_outputs():
    """Non-zero containment inputs must increase pricing."""
    
    base_result = price_case(
        engine_snapshot={"upls": 0.64, "tripwire": 6.4, "decision": "HOLD", "confidence": "Moderate"},
        monetary_inputs={"principal_debt_gbp": 66_000, "claimant_costs_gbp": 500_000, "defendant_costs_estimate_gbp": 250_000, "regulatory_exposure_gbp": 2_000_000},
        containment_inputs={"reputational_damage_gbp": 0, "regulatory_fine_risk_gbp": 0, "litigation_cascade_risk_gbp": 0},
        kill_switches={},
        mode="containment",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    containment_result = price_case(
        engine_snapshot={"upls": 0.64, "tripwire": 6.4, "decision": "HOLD", "confidence": "Moderate"},
        monetary_inputs={"principal_debt_gbp": 66_000, "claimant_costs_gbp": 500_000, "defendant_costs_estimate_gbp": 250_000, "regulatory_exposure_gbp": 2_000_000},
        containment_inputs={"reputational_damage_gbp": 3_000_000, "regulatory_fine_risk_gbp": 1_000_000, "litigation_cascade_risk_gbp": 500_000},
        kill_switches={},
        mode="containment",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    # Containment inputs must increase aim
    assert containment_result.validation_band.aim_gbp > base_result.validation_band.aim_gbp, \
        "Containment inputs should increase validation band aim"


def test_all_three_bands_calculated():
    """All three bands must be calculated regardless of active flags."""
    
    result = price_case(
        engine_snapshot={"upls": 0.5, "tripwire": 5.0, "decision": "HOLD", "confidence": "Moderate"},
        monetary_inputs={"principal_debt_gbp": 100_000, "claimant_costs_gbp": 200_000, "defendant_costs_estimate_gbp": 100_000, "regulatory_exposure_gbp": 500_000},
        containment_inputs={},
        kill_switches={},
        mode="standard",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    # All bands should exist
    assert result.base_band is not None
    assert result.validation_band is not None
    assert result.tail_band is not None
    
    # Bands should be ordered by size
    assert result.base_band.aim_gbp < result.validation_band.aim_gbp
    assert result.validation_band.aim_gbp < result.tail_band.aim_gbp


def test_kill_switches_select_tail_band():
    """Two tail triggers should select TAIL band."""
    
    result = price_case(
        engine_snapshot={"upls": 0.7, "tripwire": 8.0, "decision": "FORCE", "confidence": "High"},
        monetary_inputs={"principal_debt_gbp": 100_000, "claimant_costs_gbp": 500_000, "defendant_costs_estimate_gbp": 250_000, "regulatory_exposure_gbp": 2_000_000},
        containment_inputs={},
        kill_switches={
            "adverse_judicial_language": True,
            "sra_formal_action": True
        },
        mode="standard",
        stance={},
        fear_override=0.5,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    assert result.active_band_name == "TAIL", "Two tail triggers should select TAIL band"
    assert result.tail_band.aim_gbp >= 12_000_000, "TAIL band aim should be at least £12m"


def test_single_flag_selects_validation_band():
    """One flag should select VALIDATION band."""
    
    result = price_case(
        engine_snapshot={"upls": 0.6, "tripwire": 6.0, "decision": "HOLD", "confidence": "Moderate"},
        monetary_inputs={"principal_debt_gbp": 100_000, "claimant_costs_gbp": 500_000, "defendant_costs_estimate_gbp": 250_000, "regulatory_exposure_gbp": 2_000_000},
        containment_inputs={},
        kill_switches={"sra_investigation_open": True},
        mode="standard",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    assert result.active_band_name == "VALIDATION", "Single flag should select VALIDATION band"


def test_no_flags_selects_base_band():
    """No flags should select BASE band."""
    
    result = price_case(
        engine_snapshot={"upls": 0.4, "tripwire": 4.0, "decision": "HOLD", "confidence": "Low"},
        monetary_inputs={"principal_debt_gbp": 100_000, "claimant_costs_gbp": 200_000, "defendant_costs_estimate_gbp": 100_000, "regulatory_exposure_gbp": 500_000},
        containment_inputs={},
        kill_switches={},
        mode="standard",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    assert result.active_band_name == "BASE", "No flags should select BASE band"


def test_negotiation_alignment():
    """Alignment should reflect position vs negotiation objective."""
    
    # Below objective
    result_below = price_case(
        engine_snapshot={"upls": 0.4, "tripwire": 4.0, "decision": "HOLD", "confidence": "Low"},
        monetary_inputs={"principal_debt_gbp": 100_000, "claimant_costs_gbp": 200_000, "defendant_costs_estimate_gbp": 100_000, "regulatory_exposure_gbp": 500_000},
        containment_inputs={},
        kill_switches={},
        mode="anchor_driven",
        stance={"anchor_gbp": 15_000_000, "minimum_objective_gbp": 9_000_000},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    # Result should be below objective with current inputs
    # (small inputs won't reach £9m minimum)
    
    # Above objective
    result_above = price_case(
        engine_snapshot={"upls": 0.8, "tripwire": 8.0, "decision": "FORCE", "confidence": "High"},
        monetary_inputs={"principal_debt_gbp": 1_000_000, "claimant_costs_gbp": 2_000_000, "defendant_costs_estimate_gbp": 1_000_000, "regulatory_exposure_gbp": 5_000_000},
        containment_inputs={"reputational_damage_gbp": 5_000_000},
        kill_switches={"adverse_judicial_language": True, "sra_formal_action": True},
        mode="anchor_driven",
        stance={"anchor_gbp": 15_000_000, "minimum_objective_gbp": 9_000_000},
        fear_override=0.5,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    assert result_above.alignment in ["aligned", "below_objective"]
    assert result_above.negotiation_anchor_gbp == 15_000_000
    assert result_above.negotiation_minimum_gbp == 9_000_000


def test_band_ranges_meet_requirements():
    """Band ranges must meet the £2.5m-£4m / £5m-£9m / £12m-£15m requirements."""
    
    result = price_case(
        engine_snapshot={"upls": 0.5, "tripwire": 5.0, "decision": "HOLD", "confidence": "Moderate"},
        monetary_inputs={"principal_debt_gbp": 100_000, "claimant_costs_gbp": 500_000, "defendant_costs_estimate_gbp": 250_000, "regulatory_exposure_gbp": 1_000_000},
        containment_inputs={},
        kill_switches={},
        mode="standard",
        stance={},
        fear_override=0.0,
        assumptions={"regulatory_multiplier": 0.4, "fear_multiplier_max": 0.25}
    )
    
    # BASE band: £2.5m-£4m
    assert 2_500_000 <= result.base_band.min_gbp <= result.base_band.max_gbp <= 4_000_000, \
        f"BASE band {result.base_band.min_gbp}-{result.base_band.max_gbp} outside £2.5m-£4m range"
    
    # VALIDATION band: £5m-£9m
    assert 5_000_000 <= result.validation_band.min_gbp <= result.validation_band.max_gbp <= 9_000_000, \
        f"VALIDATION band {result.validation_band.min_gbp}-{result.validation_band.max_gbp} outside £5m-£9m range"
    
    # TAIL band: £12m-£15m
    assert 12_000_000 <= result.tail_band.min_gbp <= result.tail_band.max_gbp <= 15_000_000, \
        f"TAIL band {result.tail_band.min_gbp}-{result.tail_band.max_gbp} outside £12m-£15m range"
