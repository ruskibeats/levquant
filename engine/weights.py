"""
Explicit scoring weights.

This file makes the UPLS calculation economics explicit and version-locked.
Changing these weights alters the model economics.

Critical Design Principle:
    This file defines DEFAULT_WEIGHTS only.
    Do NOT change weights in engine/scoring.py directly.
    Import get_weights() and use WEIGHTS from here.

Version: 1.3.0
"""

from typing import Dict


# DEFAULT WEIGHTS
# These weights reflect baseline commercial-litigation risk profile
# Changing these weights modifies the model economics.
DEFAULT_WEIGHTS = {
    "sv1a": 0.40,  # Claim validity is most critical (40% weight)
    "sv1b": 0.35,  # Procedural advantage is significant (35% weight)
    "sv1c": 0.25,  # Cost asymmetry supports but doesn't dominate (25% weight)
}


def get_weights(profile: str = "default") -> Dict[str, float]:
    """
    Get weight configuration for a named profile.
    
    Args:
        profile: Name of weight profile (e.g., 'default', 'balanced')
    
    Returns:
        Dictionary of SV weights with keys sv1a, sv1b, sv1c
    
    Raises:
        ValueError: If profile is not defined
    """
    if profile == "default":
        return DEFAULT_WEIGHTS.copy()
    else:
        raise ValueError(
            f"Unknown weight profile: {profile}. "
            f"Valid profiles: default"
        )


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that weights sum to 1.0 within tolerance.
    
    Args:
        weights: Dictionary of SV weights
    
    Returns:
        True if weights sum to 1.0 within ±0.01 tolerance
    """
    total_weight = sum(weights.values())
    # Allow small floating-point tolerance
    return abs(total_weight - 1.0) < 0.01


# Export convenience function for direct access
__all__ = ["DEFAULT_WEIGHTS", "get_weights", "validate_weights"]