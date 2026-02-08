"""Pydantic schemas for the decision-support pricing layer."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Decision = Literal["ACCEPT", "HOLD", "COUNTER", "REJECT"]
Posture = Literal["NORMAL", "URGENT", "FORCE"]
SettlementObjective = Literal["standard", "containment", "anchor_driven"]


class ProceduralInputs(BaseModel):
    SV1a: float = Field(ge=0.0, le=1.0)
    SV1b: float = Field(ge=0.0, le=1.0)
    SV1c: float = Field(ge=0.0, le=1.0)


class MonetaryInputs(BaseModel):
    principal_debt_gbp: float = Field(ge=0.0)
    claimant_costs_gbp: float = Field(ge=0.0)
    defendant_costs_estimate_gbp: float = Field(ge=0.0)
    regulatory_exposure_gbp: float = Field(ge=0.0)
    transaction_value_gbp: float = Field(default=0.0, ge=0.0)
    assumptions_notes: str = ""


class ContainmentInputs(BaseModel):
    """Inputs for containment pricing mode — misconduct/regulatory risk exposure."""
    containment_exposure_gbp: float = Field(default=0.0, ge=0.0, description="Total containment exposure if misconduct becomes public")
    reputational_damage_gbp: float = Field(default=0.0, ge=0.0, description="Estimated reputational/fiduciary damage")
    regulatory_fine_risk_gbp: float = Field(default=0.0, ge=0.0, description="Potential regulatory fines (SRA, FCA, etc.)")
    litigation_cascade_risk_gbp: float = Field(default=0.0, ge=0.0, description="Risk of follow-on litigation from other claimants")


class NegotiationStance(BaseModel):
    """User-defined negotiation guardrails — separate from model valuation."""
    anchor_gbp: float = Field(default=15_000_000.0, ge=0.0, description="Opening demand / anchor position")
    minimum_objective_gbp: float = Field(default=9_000_000.0, ge=0.0, description="Walk-away minimum acceptable")
    objective_mode: SettlementObjective = Field(default="standard", description="Pricing mode: standard, containment, or anchor_driven")


class KillSwitchInputs(BaseModel):
    nullity_confirmed: bool = False
    regulatory_open: bool = False
    insurer_notice: bool = False
    override_admitted: bool = False
    shadow_director: bool = False


class EngineSnapshot(BaseModel):
    inputs: ProceduralInputs
    upls: float
    decision: Decision
    confidence: str
    tripwire: float
    tripwire_triggered: bool


class PricingBreakdownRow(BaseModel):
    component: str
    amount_gbp: float
    formula: str
    source: str
    assumption: str


class SettlementCorridor(BaseModel):
    floor_gbp: float
    base_case_gbp: float
    target_gbp: float
    ceiling_gbp: float
    delta_vs_floor_pct: float


class DualRangeCorridor(BaseModel):
    """Dual-range display: Model Range (defensible) vs Negotiation Range (stance)."""
    # Model Range — what the math says based on inputs
    model_floor_gbp: float
    model_base_gbp: float
    model_target_gbp: float
    model_ceiling_gbp: float
    
    # Negotiation Range — user's strategic stance
    negotiation_anchor_gbp: float
    negotiation_minimum_gbp: float
    
    # Pressure premium (Tripwire-driven)
    pressure_premium_gbp: float
    pressure_level: float
    urgency_multiplier_applied: float
    
    # Metadata
    objective_mode: SettlementObjective
    range_alignment: Literal["aligned", "below_objective", "above_objective"]
    explanation: str


class ScenarioResult(BaseModel):
    scenario: str
    sv1a: float
    sv1b: float
    sv1c: float
    upls: float
    decision: Decision
    tripwire: float
    floor_gbp: float
    target_gbp: float
    ceiling_gbp: float
    kill_switches_active: list[str]
    fear_index: float
    settlement_posture: Posture


class ValidationResult(BaseModel):
    name: str
    passed: bool
    expected: str
    actual: str
    rationale: str
    deviation_flag: bool


class AuditBundle(BaseModel):
    timestamp_utc: datetime
    model_version: str
    input_hash: str
    assumptions: dict
