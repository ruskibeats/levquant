"""
Current case state inputs.

This file holds the current case inputs only.
Later, this can be replaced by YAML, JSON, or database ingestion.

For now, explicit beats clever.
"""

from typing import Dict


# Current state values for the active case
CURRENT_STATE = {
    "SV1a": 0.38,
    "SV1b": 0.86,
    "SV1c": 0.75
}


def get_current_state() -> Dict[str, float]:
    """
    Retrieve the current case state.
    
    Returns:
        Dictionary containing current success vector values
    """
    return CURRENT_STATE.copy()


def validate_state(state: Dict[str, float]) -> bool:
    """
    Validate that a state dictionary has correct structure and values.
    
    Args:
        state: Dictionary with keys SV1a, SV1b, SV1c and float values
    
    Returns:
        True if state is valid, False otherwise
    """
    required_keys = {"SV1a", "SV1b", "SV1c"}
    
    # Check all required keys present
    if not required_keys.issubset(state.keys()):
        return False
    
    # Check all values are floats in valid range
    for key, value in state.items():
        if key not in required_keys:
            continue
        if not isinstance(value, (int, float)):
            return False
        if not 0.0 <= value <= 1.0:
            return False
    
    return True