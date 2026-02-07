"""Binary kill-switch definitions and FEAR index logic.

This module is additive and independent from /engine internals.
It defines metadata for binary switches and a deterministic FEAR_INDEX
derived only from active claimant-favour switches.
"""

from __future__ import annotations

from typing import Dict, List, Literal, TypedDict


Direction = Literal["claimant_favour", "defendant_favour"]


class KillSwitch(TypedDict):
    """Runtime kill-switch representation."""

    name: str
    active: bool
    severity: float
    direction: Direction
    description: str


class KillSwitchTemplate(TypedDict):
    """Template metadata for predefined kill-switches."""

    description: str
    severity: float
    direction: Direction


KILL_SWITCH_CATALOG: Dict[str, KillSwitchTemplate] = {
    "defence_nullity_confirmed": {
        "description": "Defence position invalidated at nullity level.",
        "severity": 1.00,
        "direction": "claimant_favour",
    },
    "insurer_notified_of_fraud": {
        "description": "Insurer has formal notice of potential fraud indicators.",
        "severity": 0.85,
        "direction": "claimant_favour",
    },
    "insurer_reserves_rights": {
        "description": "Insurer issues reservation-of-rights position.",
        "severity": 0.80,
        "direction": "claimant_favour",
    },
    "sra_investigation_open": {
        "description": "Regulatory investigation is actively open.",
        "severity": 0.90,
        "direction": "claimant_favour",
    },
    "police_metadata_validated": {
        "description": "Police-level metadata validation confirms evidential integrity.",
        "severity": 0.88,
        "direction": "claimant_favour",
    },
    "administrative_override_admitted": {
        "description": "Administrative override admitted on record.",
        "severity": 0.92,
        "direction": "claimant_favour",
    },
    "shadow_director_established": {
        "description": "Shadow director relationship established by evidence.",
        "severity": 0.78,
        "direction": "claimant_favour",
    },
}


def build_kill_switch(name: str, active: bool) -> KillSwitch:
    """Build a runtime kill-switch entry from catalog metadata."""
    if name not in KILL_SWITCH_CATALOG:
        raise ValueError(f"Unknown kill-switch: {name}")

    template = KILL_SWITCH_CATALOG[name]
    return {
        "name": name,
        "active": active,
        "severity": template["severity"],
        "direction": template["direction"],
        "description": template["description"],
    }


def build_kill_switch_set(active_switch_names: List[str]) -> List[KillSwitch]:
    """Return all predefined switches with active flags set explicitly."""
    active_names = set(active_switch_names)
    return [build_kill_switch(name, name in active_names) for name in KILL_SWITCH_CATALOG.keys()]


def compute_fear_index(kill_switches: List[KillSwitch]) -> float:
    """Compute FEAR_INDEX in [0.0, 1.0].

    Rules:
    - Uses only active claimant-favour switches
    - FEAR_INDEX is the maximum active severity
    - Output bounded to [0.0, 1.0]
    """
    claimant_active = [
        ks["severity"]
        for ks in kill_switches
        if ks["active"] and ks["direction"] == "claimant_favour"
    ]

    if not claimant_active:
        return 0.0

    return min(1.0, max(claimant_active))
