"""
Unified Procedural Leverage Score (UPLS) calculation.

This file contains the ONLY place where UPLS and tripwire are calculated.
No imports from anywhere else in the project.
No logging, no printing, no I/O.
Deterministic outputs only.

If this file changes, the economics changed.
"""

from typing import Tuple, Dict


def calculate_upls(sv1a: float, sv1b: float, sv1c: float) -> float:
    """
    Calculate Unified Procedural Leverage Score (UPLS).
    
    UPLS is a weighted composite of three success vector components:
    - SV1a: Claim validity strength
    - SV1b: Procedural advantage
    - SV1c: Cost asymmetry
    
    Args:
        sv1a: Success vector 1a (claim validity), range [0.0, 1.0]
        sv1b: Success vector 1b (procedural advantage), range [0.0, 1.0]
        sv1c: Success vector 1c (cost asymmetry), range [0.0, 1.0]
    
    Returns:
        UPLS score in range [0.0, 1.0]
    
    Raises:
        ValueError: If any input is outside [0.0, 1.0]
    """
    # Validate inputs
    for name, value in [("SV1a", sv1a), ("SV1b", sv1b), ("SV1c", sv1c)]:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in range [0.0, 1.0], got {value}")
    
    # Weighted composite calculation
    # Weights reflect relative importance in procedural leverage
    weight_a = 0.40  # Claim validity is most critical
    weight_b = 0.35  # Procedural advantage is significant
    weight_c = 0.25  # Cost asymmetry supports but doesn't dominate
    
    upls = (weight_a * sv1a) + (weight_b * sv1b) + (weight_c * sv1c)
    
    return round(upls, 3)


def calculate_tripwire(upls: float, base_multiplier: float = 10.0) -> float:
    """
    Calculate tripwire score for leverage threshold assessment.
    
    Tripwire provides a scaled metric for decision thresholds.
    
    Args:
        upls: Unified Procedural Leverage Score, range [0.0, 1.0]
        base_multiplier: Scaling factor (default 10.0)
    
    Returns:
        Tripwire score, typically in range [0.0, 10.0]
    
    Raises:
        ValueError: If upls is outside [0.0, 1.0]
    """
    if not 0.0 <= upls <= 1.0:
        raise ValueError(f"UPLS must be in range [0.0, 1.0], got {upls}")
    
    tripwire = upls * base_multiplier
    return round(tripwire, 2)


def calculate_comprehensive_score(
    sv1a: float,
    sv1b: float,
    sv1c: float,
    base_multiplier: float = 10.0
) -> Dict[str, float]:
    """
    Calculate both UPLS and tripwire in a single call.
    
    This is the primary entry point for scoring calculations.
    
    Args:
        sv1a: Success vector 1a (claim validity), range [0.0, 1.0]
        sv1b: Success vector 1b (procedural advantage), range [0.0, 1.0]
        sv1c: Success vector 1c (cost asymmetry), range [0.0, 1.0]
        base_multiplier: Scaling factor for tripwire (default 10.0)
    
    Returns:
        Dictionary containing:
        - 'upls': Unified Procedural Leverage Score
        - 'tripwire': Tripwire score
    
    Raises:
        ValueError: If any input is invalid
    """
    upls = calculate_upls(sv1a, sv1b, sv1c)
    tripwire = calculate_tripwire(upls, base_multiplier)
    
    return {
        'upls': upls,
        'tripwire': tripwire
    }