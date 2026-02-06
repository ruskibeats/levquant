"""
Decision logic for case evaluation.

This file translates numbers into actions (ACCEPT, COUNTER, REJECT, HOLD).
Contains thresholds, tolerances, and business logic.

Must never recompute UPLS.
"""

from typing import Literal
from enum import Enum


class Decision(Enum):
    """Enumeration of possible decisions."""
    ACCEPT = "ACCEPT"
    COUNTER = "COUNTER"
    REJECT = "REJECT"
    HOLD = "HOLD"


# Thresholds for decision-making
# These define the boundaries between different decision states
THRESHOLDS = {
    'upls_critical_low': 0.30,      # Below this: reject
    'upls_marginal': 0.50,           # Below this: counter
    'upls_acceptable': 0.70,         # Below this: hold
    'upls_strong': 0.85,             # Above this: accept
}


def evaluate_leverage(upls: float, tripwire: float) -> Decision:
    """
    Evaluate procedural leverage and determine appropriate action.
    
    Uses UPLS as primary metric, tripwire as secondary confirmation.
    
    Args:
        upls: Unified Procedural Leverage Score [0.0, 1.0]
        tripwire: Tripwire score [0.0, 10.0]
    
    Returns:
        Decision enum indicating recommended action
    
    Raises:
        ValueError: If upls or tripwire outside valid ranges
    """
    # Validate inputs
    if not 0.0 <= upls <= 1.0:
        raise ValueError(f"UPLS must be in [0.0, 1.0], got {upls}")
    if not 0.0 <= tripwire <= 10.0:
        raise ValueError(f"Tripwire must be in [0.0, 10.0], got {tripwire}")
    
    # Apply decision thresholds
    if upls < THRESHOLDS['upls_critical_low']:
        return Decision.REJECT
    elif upls < THRESHOLDS['upls_marginal']:
        return Decision.COUNTER
    elif upls < THRESHOLDS['upls_acceptable']:
        return Decision.HOLD
    elif upls >= THRESHOLDS['upls_strong']:
        return Decision.ACCEPT
    else:
        # In the acceptable but not strong range
        return Decision.HOLD


def get_decision_confidence(upls: float) -> str:
    """
    Assess confidence level in the leverage position.
    
    Args:
        upls: Unified Procedural Leverage Score [0.0, 1.0]
    
    Returns:
        String describing confidence level
    
    Raises:
        ValueError: If upls outside valid range
    """
    if not 0.0 <= upls <= 1.0:
        raise ValueError(f"UPLS must be in [0.0, 1.0], got {upls}")
    
    if upls < 0.30:
        return "Very Low"
    elif upls < 0.50:
        return "Low"
    elif upls < 0.70:
        return "Moderate"
    elif upls < 0.85:
        return "Good"
    else:
        return "Strong"


def is_tripwire_triggered(tripwire: float, threshold: float = 7.5) -> bool:
    """
    Check if tripwire threshold is triggered.
    
    Args:
        tripwire: Tripwire score [0.0, 10.0]
        threshold: Trigger threshold (default 7.5)
    
    Returns:
        True if tripwire is triggered, False otherwise
    """
    return tripwire >= threshold


def get_risk_assessment(upls: float, tripwire: float) -> dict:
    """
    Comprehensive risk assessment based on scores.
    
    Args:
        upls: Unified Procedural Leverage Score [0.0, 1.0]
        tripwire: Tripwire score [0.0, 10.0]
    
    Returns:
        Dictionary with risk assessment details
    """
    decision = evaluate_leverage(upls, tripwire)
    confidence = get_decision_confidence(upls)
    triggered = is_tripwire_triggered(tripwire)
    
    return {
        'decision': decision.value,
        'confidence': confidence,
        'tripwire_triggered': triggered,
        'upls_value': upls,
        'tripwire_value': tripwire
    }