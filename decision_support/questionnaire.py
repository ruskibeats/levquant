"""Input pack builders for decision-support workflow."""

from __future__ import annotations

from .schemas import KillSwitchInputs, MonetaryInputs, ProceduralInputs


def default_procedural_inputs() -> ProceduralInputs:
    return ProceduralInputs(SV1a=0.38, SV1b=0.86, SV1c=0.75)


def default_monetary_inputs() -> MonetaryInputs:
    return MonetaryInputs(
        principal_debt_gbp=66_000,
        claimant_costs_gbp=500_000,
        defendant_costs_estimate_gbp=250_000,
        regulatory_exposure_gbp=0,
        transaction_value_gbp=0,
        assumptions_notes="Baseline assumptions for structured settlement corridor.",
    )


def default_kill_switch_inputs() -> KillSwitchInputs:
    return KillSwitchInputs(
        nullity_confirmed=False,
        regulatory_open=False,
        insurer_notice=False,
        override_admitted=False,
        shadow_director=False,
    )
