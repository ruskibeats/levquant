"""
Named scenario presets for what-if analysis.

These presets provide quick access to predefined state configurations,
making the tool immediately more useful for settlement negotiations
and client presentations.

Version: 1.0
"""

from typing import Dict


PRESETS = {
    "baseline": {
        "name": "Baseline - Current Case",
        "state": {"SV1a": 0.38, "SV1b": 0.86, "SV1c": 0.75},
        "description": "Current case inputs - reference baseline for comparison"
    },
    
    "authority_collapse": {
        "name": "Authority Defect Confirmed",
        "state": {"SV1a": 0.15, "SV1b": 0.86, "SV1c": 0.75},
        "description": "HMCTS audit reveals definitive authority defects (catastrophic)"
    },
    
    "procedural_win": {
        "name": "Procedural Arguments Succeed",
        "state": {"SV1a": 0.38, "SV1b": 0.95, "SV1c": 0.75},
        "description": "Court accepts procedural leverage arguments"
    },
    
    "cost_spike": {
        "name": "Cost Asymmetry Spike",
        "state": {"SV1a": 0.38, "SV1b": 0.86, "SV1c": 0.95},
        "description": "Defendant costs escalate, indemnity costs likely"
    },
    
    "nuclear": {
        "name": "Everything Goes Wrong",
        "state": {"SV1a": 0.15, "SV1b": 0.20, "SV1c": 0.25},
        "description": "Worst-case across all vectors (authority+procedure+costs)"
    }
}


def get_preset(name: str) -> dict:
    """
    Load a named scenario preset.
    
    Args:
        name: Name of the preset to load
    
    Returns:
        Dictionary containing name, state, and description
    
    Raises:
        ValueError: If preset name is not defined
    """
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Valid presets: {list_presets()}")
    
    return PRESETS[name]


def list_presets() -> list[str]:
    """
    List all available scenario presets.
    
    Returns:
        List of preset names
    """
    return list(PRESETS.keys())