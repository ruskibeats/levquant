"""
Named scenario presets.

Pre-defined states for common situations.
Quick reference without manual state construction.
"""

from typing import Dict


# Preset scenarios for common situations
PRESETS = {
    'baseline': {
        'SV1a': 0.38,
        'SV1b': 0.86,
        'SV1c': 0.75
    },
    'strong_position': {
        'SV1a': 0.85,
        'SV1b': 0.90,
        'SV1c': 0.80
    },
    'weak_position': {
        'SV1a': 0.25,
        'SV1b': 0.30,
        'SV1c': 0.35
    },
    'balanced_dispute': {
        'SV1a': 0.50,
        'SV1b': 0.50,
        'SV1c': 0.50
    },
    'procedural_advantage_only': {
        'SV1a': 0.40,
        'SV1b': 0.95,
        'SV1c': 0.45
    },
    'claim_validity_only': {
        'SV1a': 0.95,
        'SV1b': 0.40,
        'SV1c': 0.45
    },
    'cost_advantage_only': {
        'SV1a': 0.40,
        'SV1b': 0.45,
        'SV1c': 0.95
    }
}


def get_preset(name: str) -> Dict[str, float]:
    """
    Retrieve a named preset scenario.
    
    Args:
        name: Name of the preset (e.g., 'baseline', 'strong_position')
    
    Returns:
        Dictionary with SV1a, SV1b, SV1c values
    
    Raises:
        KeyError: If preset name not found
    """
    if name not in PRESETS:
        available = ', '.join(sorted(PRESETS.keys()))
        raise KeyError(
            f"Preset '{name}' not found. Available presets: {available}"
        )
    
    return PRESETS[name].copy()


def list_presets() -> list:
    """
    Get list of available preset names.
    
    Returns:
        List of preset names
    """
    return sorted(PRESETS.keys())


def create_custom_preset(name: str, sv1a: float, sv1b: float, sv1c: float) -> None:
    """
    Create a new custom preset.
    
    Args:
        name: Name for the new preset
        sv1a: SV1a value
        sv1b: SV1b value
        sv1c: SV1c value
    
    Raises:
        ValueError: If any value is outside [0.0, 1.0]
    """
    for var_name, value in [("SV1a", sv1a), ("SV1b", sv1b), ("SV1c", sv1c)]:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{var_name} must be in [0.0, 1.0], got {value}")
    
    PRESETS[name] = {
        'SV1a': sv1a,
        'SV1b': sv1b,
        'SV1c': sv1c
    }