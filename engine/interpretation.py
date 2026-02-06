"""
Human-readable labels and interpretations.

This file converts scores into language.
Keeps language out of the maths, which is critical.
"""

from typing import Dict


def interpret_upls_range(upls: float) -> str:
    """
    Provide human-readable interpretation of UPLS value.
    
    Args:
        upls: Unified Procedural Leverage Score [0.0, 1.0]
    
    Returns:
        Human-readable description of leverage position (posture, not outcome)
    """
    if upls < 0.30:
        return "Low procedural leverage - weak positioning"
    elif upls < 0.50:
        return "Limited leverage - defensive posture required"
    elif upls < 0.70:
        return "Moderate leverage - routine dispute parameters"
    elif upls < 0.85:
        return "Strong leverage - favorable negotiating position"
    else:
        return "Very high procedural leverage - upper-bound positioning"


def interpret_decision(decision: str) -> str:
    """
    Provide human-readable explanation of decision.
    
    Args:
        decision: Decision string (ACCEPT, COUNTER, REJECT, HOLD)
    
    Returns:
        Human-readable description of recommended action (descriptive, not justificatory)
    """
    interpretations = {
        'ACCEPT': (
            "Model indicates acceptance is consistent with current leverage posture."
        ),
        'COUNTER': (
            "Model indicates counter-offer is appropriate given current leverage posture."
        ),
        'REJECT': (
            "Model indicates rejection is consistent with current leverage posture."
        ),
        'HOLD': (
            "Model indicates maintaining position is appropriate given current leverage posture."
        )
    }
    
    return interpretations.get(decision, "Unknown decision")


def interpret_tripwire(tripwire: float) -> str:
    """
    Provide human-readable interpretation of tripwire status.
    
    Args:
        tripwire: Tripwire score [0.0, 10.0]
    
    Returns:
        Human-readable description of tripwire status (assessment, not prediction)
    """
    if tripwire < 5.0:
        return "Safe zone - no immediate procedural concerns"
    elif tripwire < 7.5:
        return "Caution zone - monitor for changes"
    else:
        return "Critical zone - tripwire triggered, elevated attention required"


def interpret_confidence(confidence: str) -> str:
    """
    Provide human-readable interpretation of confidence level.
    
    Args:
        confidence: Confidence string from evaluation layer
    
    Returns:
        Human-readable description of confidence level
    """
    confidence_map = {
        'Very Low': 'Model indicates low confidence in current leverage assessment.',
        'Low': 'Model indicates limited confidence in current leverage assessment.',
        'Moderate': 'Model indicates moderate confidence in current leverage assessment.',
        'Good': 'Model indicates good confidence in current leverage assessment.',
        'Strong': 'Model indicates strong confidence in current leverage assessment.'
    }
    return confidence_map.get(confidence, 'Unknown confidence level')


def get_full_interpretation(upls: float, tripwire: float, decision: str, confidence: str) -> Dict[str, str]:
    """
    Compile comprehensive human-readable interpretation.
    
    Args:
        upls: Unified Procedural Leverage Score [0.0, 1.0]
        tripwire: Tripwire score [0.0, 10.0]
        decision: Decision string
        confidence: Confidence string from evaluation layer
    
    Returns:
        Dictionary with all human-readable interpretations
    """
    return {
        'leverage_position': interpret_upls_range(upls),
        'decision_explanation': interpret_decision(decision),
        'tripwire_status': interpret_tripwire(tripwire),
        'confidence_explanation': interpret_confidence(confidence)
    }


def format_summary(state: Dict, scores: Dict, risk_assessment: Dict) -> str:
    """
    Format a clean, human-readable summary of the case analysis.
    
    Args:
        state: Current state dictionary
        scores: Scores dictionary with upls and tripwire
        risk_assessment: Risk assessment dictionary
    
    Returns:
        Formatted summary string
    """
    # Helper function for safe formatting
    def format_float(value, default='N/A', precision='.3f'):
        if isinstance(value, (int, float)):
            return f"{value:{precision}}"
        return default
    
    lines = [
        "=" * 60,
        "PROCEDURAL LEVERAGE ENGINE - CASE ANALYSIS",
        "=" * 60,
        "",
        "INPUTS:",
        f"  SV1a (Claim Validity): {format_float(state.get('SV1a'), 'N/A', '.2f')}",
        f"  SV1b (Procedural Advantage): {format_float(state.get('SV1b'), 'N/A', '.2f')}",
        f"  SV1c (Cost Asymmetry): {format_float(state.get('SV1c'), 'N/A', '.2f')}",
        "",
        "SCORES:",
        f"  UPLS: {format_float(scores.get('upls'), 'N/A', '.3f')}",
        f"  Tripwire: {format_float(scores.get('tripwire'), 'N/A', '.2f')}",
        "",
        "DECISION:",
        f"  Action: {risk_assessment.get('decision', 'N/A')}",
        f"  Confidence: {risk_assessment.get('confidence', 'N/A')}",
        f"  Tripwire Triggered: {'Yes' if risk_assessment.get('tripwire_triggered') else 'No'}",
        "",
        "INTERPRETATION:",
        f"  {interpret_upls_range(scores.get('upls', 0))}",
        "",
        "=" * 60
    ]
    
    return "\n".join(lines)