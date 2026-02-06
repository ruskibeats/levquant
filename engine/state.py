"""
Current case state inputs.

This file holds the current case inputs only.
Later, this can be replaced by YAML, JSON, or database ingestion.

For now, explicit beats clever.
"""

from typing import Dict, Optional, Any
import copy


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


def load_state(state_dict: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Load external state dictionary with validation.
    
    Args:
        state_dict: Optional dictionary containing SV1a, SV1b, SV1c values
                     (e.g., from YAML, JSON, or database ingestion)
                     If None, return current case state
    
    Returns:
        Validated state dictionary
    
    Raises:
        ValueError: With clear message if state_dict is invalid
    """
    # If state_dict is None, return current case state
    if state_dict is None:
        return get_current_state()
    
    # Validate state dictionary
    if not validate_state(state_dict):
        raise ValueError(f"Invalid state: {state_dict}")
    
    # Return a deep copy (not a reference to maintain immutability)
    return copy.deepcopy(state_dict)


def validate_state(state: Dict[str, float]) -> bool:
    """
    Validate that a state dictionary has correct structure and values.
    
    Args:
        state: Dictionary with keys SV1a, SV1b, SV1c and float values
    
    Returns:
        True if state is valid, False otherwise
    """
    required_keys = {"SV1a", "SV1b", "SV1c"}
    
    # Check all required keys are present
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