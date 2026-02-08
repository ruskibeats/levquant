"""Deterministic monetary translation layer for settlement corridor pricing.

This module is intentionally outside `/engine` and consumes deterministic
outputs via `cli.run.run_engine` only.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO

import matplotlib.pyplot as plt

from cli.run import VERSION, run_engine
from scenarios.kill_switches import build_kill_switch_set, compute_fear_index

from .schemas import (
    AuditBundle,
    ContainmentInputs,
    DualRangeCorridor,
    EngineSnapshot,
    KillSwitchInputs,
    MonetaryInputs,
    NegotiationStance,
    PricingBreakdownRow,
    ProceduralInputs,
    SettlementCorridor,
)


ASSUMPTIONS = {
    "leverage_multiplier_min": 0.05,
    "leverage_multiplier_max": 0.35,
    "urgency_multiplier": {"NORMAL": 0.00, "URGENT": 0.10, "FORCE": 0.20},
    "regulatory_multiplier": 0.40,
    "transaction_multiplier": 0.03,
    "fear_multiplier_max": 0.25,
    "ceiling_buffer": 0.12,
    "containment_multiplier": 0.65,
    "pressure_premium_base": 0.05,
    # Event escalation rules (regime-change assumptions)
    "event_escalation_rules": {
        "pressure_rebase_thresholds": [1, 3],
        "floor_rebase_rules": [
            "defence_nullity_confirmed",
            "sra_investigation_open", 
            "insurer_notified_of_fraud"
        ],
        "ceiling_expansion_steps": [2, 4],
        "stress_override_forces_max": True,
        "description": "These are regime-change assumptions, not incremental adjustments"
    },
    "pressure_floor_by_event_count": {1: 7.5, 3: 8.5},
    "pressure_override_admitted": 9.5,
    "ceiling_expansion_multipliers": {2: 1.6, 4: 2.2},
    "floor_rebase_multipliers": {
        "defence_nullity_confirmed": 1.5,
        "sra_investigation_open": 0.35,  # Applied to containment_exposure
        "insurer_notified_of_fraud": 0.45,  # Applied to containment_exposure
    }
}


def _map_ui_kill_switches(k: KillSwitchInputs) -> list[str]:
    mapping = {
        "nullity_confirmed": "defence_nullity_confirmed",
        "regulatory_open": "sra_investigation_open",
        "insurer_notice": "insurer_notified_of_fraud",
        "override_admitted": "administrative_override_admitted",
        "shadow_director": "shadow_director_established",
    }
    active = []
    for ui_name, catalog_name in mapping.items():
        if getattr(k, ui_name):
            active.append(catalog_name)
    return active


def get_engine_snapshot(proc: ProceduralInputs) -> EngineSnapshot:
    result = run_engine(state=proc.model_dump())
    return EngineSnapshot(
        inputs=ProceduralInputs(**result["inputs"]),
        upls=result["scores"]["upls"],
        decision=result["evaluation"]["decision"],
        confidence=result["evaluation"]["confidence"],
        tripwire=result["scores"]["tripwire"],
        tripwire_triggered=result["evaluation"]["tripwire_triggered"],
    )


def settlement_posture(engine: EngineSnapshot, fear_index: float) -> str:
    if fear_index >= 0.90 or engine.tripwire >= 8.5:
        return "FORCE"
    if fear_index >= 0.75 or engine.tripwire >= 7.5:
        return "URGENT"
    return "NORMAL"


def calculate_pressure_premium(
    core_base: float,
    pressure_level: float,
    posture: str,
) -> tuple[float, float]:
    """Calculate Tripwire-driven pressure premium.
    
    Formula: pressure_premium = core_base × urgency_multiplier(posture) × (pressure_level / 10)
    
    Returns:
        Tuple of (premium_amount, applied_multiplier)
    """
    urgency_mult = ASSUMPTIONS["urgency_multiplier"].get(posture, 0.0)
    pressure_factor = pressure_level / 10.0
    applied_multiplier = urgency_mult * pressure_factor
    premium = core_base * applied_multiplier
    return premium, applied_multiplier


def apply_event_escalation(
    engine: EngineSnapshot,
    active_events: list[str],
    fear_index: float,
    stress_override: float | None,
) -> tuple[float, float, str, list[str]]:
    """Apply event-driven pressure escalation and regime changes.
    
    This is where Events That Change Everything actually change everything.
    Operates outside the engine — modifies derived pressure, not engine truth.
    
    Returns:
        Tuple of (adjusted_pressure, adjusted_fear, adjusted_posture, applied_rules)
    """
    pressure_level = engine.tripwire
    applied_rules = []
    
    # B. Mandatory Pressure Level Escalation by event count
    event_count = len(active_events)
    
    if event_count >= 1:
        new_pressure = ASSUMPTIONS["pressure_floor_by_event_count"][1]
        if pressure_level < new_pressure:
            pressure_level = new_pressure
            applied_rules.append(f"pressure_rebase: {event_count} events → floor at {new_pressure}")
    
    if event_count >= 3:
        new_pressure = ASSUMPTIONS["pressure_floor_by_event_count"][3]
        if pressure_level < new_pressure:
            pressure_level = new_pressure
            applied_rules.append(f"pressure_rebase: {event_count} events → floor at {new_pressure}")
    
    # Administrative override admitted = maximum pressure
    if "administrative_override_admitted" in active_events:
        pressure_level = ASSUMPTIONS["pressure_override_admitted"]
        applied_rules.append(f"pressure_override: administrative_override_admitted → {pressure_level}")
    
    # E. Weakest-Link Stress Override forces maximum
    if stress_override is not None and stress_override >= 1.0:
        fear_index = 1.0
        applied_rules.append("stress_override: forced fear_index to 1.0 (maximum)")
    
    # Determine posture based on escalated values
    if fear_index >= 0.90 or pressure_level >= 8.5:
        posture = "FORCE"
    elif fear_index >= 0.75 or pressure_level >= 7.5:
        posture = "URGENT"
    else:
        posture = "NORMAL"
    
    if posture in ["URGENT", "FORCE"]:
        applied_rules.append(f"posture_lock: escalated to {posture}")
    
    return pressure_level, fear_index, posture, applied_rules


def apply_corridor_rebase(
    floor: float,
    ceiling: float,
    active_events: list[str],
    core_cost_base: float,
    containment_exposure: float,
) -> tuple[float, float, list[str]]:
    """Apply event-driven corridor re-basing and ceiling expansion.
    
    C. Corridor Re-basing (Critical Fix) — floor jumps, not grows linearly
    D. Ceiling Expansion (Non-Linear) — stepwise, not gradual
    
    Returns:
        Tuple of (adjusted_floor, adjusted_ceiling, applied_rules)
    """
    applied_rules = []
    event_count = len(active_events)
    
    # C. Floor re-basing based on specific events
    rebase_multipliers = ASSUMPTIONS["floor_rebase_multipliers"]
    
    if "defence_nullity_confirmed" in active_events:
        new_floor = core_cost_base * rebase_multipliers["defence_nullity_confirmed"]
        if new_floor > floor:
            floor = new_floor
            applied_rules.append(f"floor_rebase: defence_nullity_confirmed → {new_floor:,.0f}")
    
    if "sra_investigation_open" in active_events and containment_exposure > 0:
        new_floor = containment_exposure * rebase_multipliers["sra_investigation_open"]
        if new_floor > floor:
            floor = new_floor
            applied_rules.append(f"floor_rebase: sra_investigation_open → {new_floor:,.0f}")
    
    if "insurer_notified_of_fraud" in active_events and containment_exposure > 0:
        new_floor = containment_exposure * rebase_multipliers["insurer_notified_of_fraud"]
        if new_floor > floor:
            floor = new_floor
            applied_rules.append(f"floor_rebase: insurer_notified_of_fraud → {new_floor:,.0f}")
    
    # D. Ceiling expansion stepwise
    expansion_multipliers = ASSUMPTIONS["ceiling_expansion_multipliers"]
    
    if event_count >= 4:
        old_ceiling = ceiling
        ceiling *= expansion_multipliers[4]
        applied_rules.append(f"ceiling_expansion: {event_count} events → {expansion_multipliers[4]}x ({old_ceiling:,.0f} → {ceiling:,.0f})")
    elif event_count >= 2:
        old_ceiling = ceiling
        ceiling *= expansion_multipliers[2]
        applied_rules.append(f"ceiling_expansion: {event_count} events → {expansion_multipliers[2]}x ({old_ceiling:,.0f} → {ceiling:,.0f})")
    
    return floor, ceiling, applied_rules


def build_pricing(
    proc: ProceduralInputs,
    money: MonetaryInputs,
    kill_switches: KillSwitchInputs,
    fear_override: float | None = None,
    containment: ContainmentInputs | None = None,
    stance: NegotiationStance | None = None,
) -> dict:
    engine = get_engine_snapshot(proc)
    active_catalog = _map_ui_kill_switches(kill_switches)
    kill_switch_set = build_kill_switch_set(active_catalog)
    catalog_fear = compute_fear_index(kill_switch_set)
    fear_index = max(catalog_fear, fear_override or 0.0)
    fear_index = min(1.0, fear_index)

    containment = containment or ContainmentInputs()
    stance = stance or NegotiationStance()

    # Apply event escalation BEFORE posture determination
    # This is where Events That Change Everything actually change everything
    adjusted_pressure, adjusted_fear, posture, escalation_rules = apply_event_escalation(
        engine=engine,
        active_events=active_catalog,
        fear_index=max(catalog_fear, fear_override or 0.0),
        stress_override=fear_override,
    )
    
    # Update engine snapshot with escalated values (outside /engine)
    engine = EngineSnapshot(
        inputs=engine.inputs,
        upls=engine.upls,
        decision=engine.decision,
        confidence=engine.confidence,
        tripwire=adjusted_pressure,  # Escalated pressure
        tripwire_triggered=engine.tripwire_triggered or adjusted_pressure >= 7.5,
    )
    fear_index = adjusted_fear

    # Core base calculation
    core_base = money.principal_debt_gbp + money.claimant_costs_gbp + money.defendant_costs_estimate_gbp
    core_cost_base = money.claimant_costs_gbp + money.defendant_costs_estimate_gbp
    
    # Standard premiums
    leverage_mult = ASSUMPTIONS["leverage_multiplier_min"] + (
        (ASSUMPTIONS["leverage_multiplier_max"] - ASSUMPTIONS["leverage_multiplier_min"]) * engine.upls
    )
    leverage_premium = core_base * leverage_mult
    
    # Tripwire-driven pressure premium (NEW)
    pressure_premium, applied_pressure_mult = calculate_pressure_premium(
        core_base, engine.tripwire, posture
    )
    
    regulatory_premium = money.regulatory_exposure_gbp * ASSUMPTIONS["regulatory_multiplier"]
    transaction_premium = money.transaction_value_gbp * ASSUMPTIONS["transaction_multiplier"]
    fear_premium = core_base * ASSUMPTIONS["fear_multiplier_max"] * fear_index
    
    # Containment premiums (NEW) — only applied in containment or anchor_driven modes
    containment_premium = 0.0
    if stance.objective_mode in ("containment", "anchor_driven"):
        containment_premium = (
            containment.containment_exposure_gbp * ASSUMPTIONS["containment_multiplier"] +
            containment.reputational_damage_gbp * 0.5 +
            containment.regulatory_fine_risk_gbp * 0.6 +
            containment.litigation_cascade_risk_gbp * 0.4
        )

    # Standard model corridor (before event rebase)
    floor = max(0.0, core_base)
    base_case = floor + leverage_premium + regulatory_premium + pressure_premium
    target = base_case + transaction_premium + fear_premium + containment_premium
    ceiling = target * (1.0 + ASSUMPTIONS["ceiling_buffer"])
    
    # C & D. Apply event-driven corridor re-basing (regime change)
    total_containment_exposure = (
        containment.containment_exposure_gbp +
        containment.reputational_damage_gbp +
        containment.regulatory_fine_risk_gbp +
        containment.litigation_cascade_risk_gbp
    )
    
    floor, ceiling, rebase_rules = apply_corridor_rebase(
        floor=floor,
        ceiling=ceiling,
        active_events=active_catalog,
        core_cost_base=core_cost_base,
        containment_exposure=total_containment_exposure,
    )
    
    # Recalculate target/ceiling after floor rebase
    target = max(target, floor * 1.2)  # Ensure target is above rebased floor
    ceiling = max(ceiling, target * 1.1)  # Ensure ceiling is above target
    delta_pct = ((target - floor) / floor * 100.0) if floor > 0 else 0.0
    
    # Dual-range corridor (NEW)
    dual_corridor = _build_dual_corridor(
        model_floor=floor,
        model_base=base_case,
        model_target=target,
        model_ceiling=ceiling,
        stance=stance,
        pressure_premium=pressure_premium,
        pressure_level=engine.tripwire,
        applied_multiplier=applied_pressure_mult,
    )

    breakdown = [
        PricingBreakdownRow(
            component="Debt + costs",
            amount_gbp=core_base,
            formula="principal + claimant_costs + defendant_costs",
            source="Monetary inputs",
            assumption="Direct hard costs baseline",
        ),
        PricingBreakdownRow(
            component="Leverage premium",
            amount_gbp=leverage_premium,
            formula="core_base * leverage_multiplier",
            source="UPLS from deterministic engine",
            assumption=f"Multiplier band {ASSUMPTIONS['leverage_multiplier_min']:.2f}–{ASSUMPTIONS['leverage_multiplier_max']:.2f}",
        ),
        PricingBreakdownRow(
            component="Pressure premium (Tripwire)",
            amount_gbp=pressure_premium,
            formula="core_base * urgency_multiplier(posture) * (pressure_level/10)",
            source=f"Pressure Level {engine.tripwire:.1f}/10",
            assumption=f"As pressure rises, cost of delay rises. Applied multiplier: {applied_pressure_mult:.3f}",
        ),
        PricingBreakdownRow(
            component="Regulatory premium",
            amount_gbp=regulatory_premium,
            formula="regulatory_exposure * regulatory_multiplier",
            source="Monetary inputs",
            assumption=f"Regulatory multiplier {ASSUMPTIONS['regulatory_multiplier']:.2f}",
        ),
        PricingBreakdownRow(
            component="Transaction premium",
            amount_gbp=transaction_premium,
            formula="transaction_value * transaction_multiplier",
            source="Monetary inputs",
            assumption=f"Transaction multiplier {ASSUMPTIONS['transaction_multiplier']:.2f}",
        ),
        PricingBreakdownRow(
            component="Fear premium",
            amount_gbp=fear_premium,
            formula="core_base * fear_multiplier_max * fear_index",
            source="Kill-switch and optional override",
            assumption=f"fear_multiplier_max={ASSUMPTIONS['fear_multiplier_max']:.2f}, fear_index={fear_index:.2f}",
        ),
    ]
    
    # Add containment premium to breakdown if applicable
    if containment_premium > 0:
        breakdown.append(
            PricingBreakdownRow(
                component="Containment premium",
                amount_gbp=containment_premium,
                formula="containment_exposure * 0.65 + reputational * 0.5 + fines * 0.6 + cascade * 0.4",
                source="Containment inputs",
                assumption=f"Mode: {stance.objective_mode}, containment_multiplier={ASSUMPTIONS['containment_multiplier']:.2f}",
            )
        )

    corridor = SettlementCorridor(
        floor_gbp=round(floor, 2),
        base_case_gbp=round(base_case, 2),
        target_gbp=round(target, 2),
        ceiling_gbp=round(ceiling, 2),
        delta_vs_floor_pct=round(delta_pct, 2),
    )

    return {
        "engine": engine,
        "corridor": corridor,
        "dual_corridor": dual_corridor,
        "breakdown": breakdown,
        "posture": posture,
        "fear_index": fear_index,
        "kill_switches_active": active_catalog,
        "containment": containment,
        "stance": stance,
    }


def _build_dual_corridor(
    model_floor: float,
    model_base: float,
    model_target: float,
    model_ceiling: float,
    stance: NegotiationStance,
    pressure_premium: float,
    pressure_level: float,
    applied_multiplier: float,
) -> DualRangeCorridor:
    """Build the dual-range corridor showing both model and negotiation ranges."""
    
    # Determine alignment status
    if model_target < stance.minimum_objective_gbp * 0.5:
        alignment = "below_objective"
        explanation = (
            f"Model Target (£{model_target:,.0f}) is significantly below your "
            f"Minimum Objective (£{stance.minimum_objective_gbp:,.0f}). "
            "Consider: (1) Switch to 'containment' or 'anchor_driven' mode, "
            "(2) Add containment exposure inputs, or (3) Review if this is a standard dispute vs. misconduct case."
        )
    elif model_target >= stance.minimum_objective_gbp:
        alignment = "aligned"
        explanation = (
            f"Model Target (£{model_target:,.0f}) meets or exceeds your "
            f"Minimum Objective (£{stance.minimum_objective_gbp:,.0f}). "
            "The model inputs support your negotiation stance."
        )
    else:
        alignment = "below_objective"
        explanation = (
            f"Model Target (£{model_target:,.0f}) is below your "
            f"Minimum Objective (£{stance.minimum_objective_gbp:,.0f}) but within range. "
            "Consider adding containment exposure or increasing regulatory/transaction inputs."
        )
    
    return DualRangeCorridor(
        model_floor_gbp=round(model_floor, 2),
        model_base_gbp=round(model_base, 2),
        model_target_gbp=round(model_target, 2),
        model_ceiling_gbp=round(model_ceiling, 2),
        negotiation_anchor_gbp=stance.anchor_gbp,
        negotiation_minimum_gbp=stance.minimum_objective_gbp,
        pressure_premium_gbp=round(pressure_premium, 2),
        pressure_level=pressure_level,
        urgency_multiplier_applied=applied_multiplier,
        objective_mode=stance.objective_mode,
        range_alignment=alignment,
        explanation=explanation,
    )


def detect_low_range_causes(
    money: MonetaryInputs,
    containment: ContainmentInputs,
    stance: NegotiationStance,
) -> list[str]:
    """Detect why the model range might be low and provide plain English explanations.
    
    Returns a list of actionable observations.
    """
    causes = []
    
    # Check if containment inputs are zero when in containment/anchor mode
    if stance.objective_mode in ("containment", "anchor_driven"):
        total_containment = (
            containment.containment_exposure_gbp +
            containment.reputational_damage_gbp +
            containment.regulatory_fine_risk_gbp +
            containment.litigation_cascade_risk_gbp
        )
        if total_containment == 0:
            causes.append(
                "Your containment inputs are currently zero, so the dashboard is pricing this as a standard dispute. "
                "Add containment exposure (misconduct/regulatory risk) to scale the corridor toward your £9m+ objective."
            )
    
    # Check regulatory exposure
    if money.regulatory_exposure_gbp == 0:
        causes.append(
            "Regulatory exposure is £0. If regulatory investigation is a risk, add estimated exposure to increase the model range."
        )
    
    # Check transaction value
    if money.transaction_value_gbp == 0:
        causes.append(
            "Transaction value is £0. For cases involving transaction-related claims, add the transaction value."
        )
    
    # Check defendant costs
    if money.defendant_costs_estimate_gbp < 500_000:
        causes.append(
            f"Defendant costs estimate (£{money.defendant_costs_estimate_gbp:,.0f}) is low for a big containment fight. "
            "For high-stakes litigation, defendant costs often exceed £1-2m."
        )
    
    # Mode-specific guidance
    if stance.objective_mode == "standard" and stance.minimum_objective_gbp >= 9_000_000:
        causes.append(
            "You are in 'standard' mode but have a £9m+ minimum objective. "
            "Switch to 'containment' or 'anchor_driven' mode to access containment pricing."
        )
    
    return causes


def build_audit_bundle(payload: dict) -> AuditBundle:
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return AuditBundle(
        timestamp_utc=datetime.now(UTC),
        model_version=VERSION,
        input_hash=hashlib.sha256(canonical).hexdigest(),
        assumptions=ASSUMPTIONS,
    )


def build_pdf_summary(report: dict) -> bytes:
    """Generate a simple court-safe PDF summary for download."""
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_subplot(111)
    ax.axis("off")
    
    # Dual corridor extraction
    dual = report.get("dual_corridor")
    
    lines = [
        "LEVQUANT COURT-READY SUMMARY",
        f"Timestamp: {datetime.now(UTC).isoformat()}",
        "",
        "=== DECISION SUPPORT OUTPUT ===",
        f"Recommended Action (Decision): {report['engine']['decision']}",
        f"Position Strength (UPLS): {report['engine']['upls']:.3f}",
        f"Pressure Level (Tripwire): {report['engine']['tripwire']:.2f}",
        f"Stance (Posture): {report['posture']}",
        f"Weakest-Link Stress Level (Fear Index): {report['fear_index']:.2f}",
        "",
    ]
    
    # Add dual range if available
    if dual:
        lines.extend([
            "=== MODEL RANGE (Input-Driven) ===",
            f"Minimum Offer (Floor): £{dual['model_floor_gbp']:,.2f}",
            f"Aim Offer (Target): £{dual['model_target_gbp']:,.2f}",
            f"Maximum Offer (Ceiling): £{dual['model_ceiling_gbp']:,.2f}",
            "",
            "=== NEGOTIATION RANGE (Strategic Stance) ===",
            f"Opening Demand (Anchor): £{dual['negotiation_anchor_gbp']:,.2f}",
            f"Walk-Away Minimum: £{dual['negotiation_minimum_gbp']:,.2f}",
            f"Objective Mode: {dual['objective_mode']}",
            "",
        ])
        if dual.get('pressure_premium_gbp', 0) > 0:
            lines.append(f"Pressure Premium Applied: £{dual['pressure_premium_gbp']:,.2f}")
            lines.append("")
    else:
        lines.extend([
            "=== SETTLEMENT RANGE ===",
            f"Minimum Offer (Floor): £{report['corridor']['floor_gbp']:,.2f}",
            f"Aim Offer (Target): £{report['corridor']['target_gbp']:,.2f}",
            f"Maximum Offer (Ceiling): £{report['corridor']['ceiling_gbp']:,.2f}",
            "",
        ])
    
    lines.extend([
        "=== COURT-SAFE DISCLAIMERS ===",
        "• Model Range is a decision-support calculation based on explicit, quantified inputs.",
        "• Negotiation Range reflects strategic positioning and requires separate justification.",
        "• This output does not claim to 'prove' any specific settlement value.",
        "• The model is deterministic: same inputs always produce same outputs.",
        "• All assumptions are listed in the dashboard 'What This Is Based On' panel.",
        "",
        "This is a decision-support tool and not legal advice.",
    ])
    
    ax.text(0.02, 0.98, "\n".join(lines), va="top", ha="left", fontsize=10, family="monospace")
    buf = BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
