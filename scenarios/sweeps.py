"""
SV sweeps and what-if scenarios.

Run hypothetical states without touching the live one.
Examples: "Judge hostile", "Costs spike", "Invalidity collapses"

Nothing in here should be required for day-to-day use.
"""

from typing import List, Dict, Tuple


def sweep_sv1a(base_state: Dict[str, float], steps: int = 20) -> List[Dict]:
    """
    Sweep SV1a (claim validity) across its full range while holding others constant.
    
    Useful for: Assessing sensitivity to claim strength
    
    Args:
        base_state: Base state dictionary with SV1a, SV1b, SV1c values
        steps: Number of steps in the sweep (default 20)
    
    Returns:
        List of state dictionaries with varying SV1a values
    """
    results = []
    sv1b_base = base_state.get('SV1b', 0.5)
    sv1c_base = base_state.get('SV1c', 0.5)
    
    for i in range(steps + 1):
        sv1a = i / steps
        results.append({
            'SV1a': round(sv1a, 2),
            'SV1b': sv1b_base,
            'SV1c': sv1c_base
        })
    
    return results


def sweep_sv1b(base_state: Dict[str, float], steps: int = 20) -> List[Dict]:
    """
    Sweep SV1b (procedural advantage) across its full range while holding others constant.
    
    Useful for: Assessing sensitivity to procedural positioning
    
    Args:
        base_state: Base state dictionary with SV1a, SV1b, SV1c values
        steps: Number of steps in the sweep (default 20)
    
    Returns:
        List of state dictionaries with varying SV1b values
    """
    results = []
    sv1a_base = base_state.get('SV1a', 0.5)
    sv1c_base = base_state.get('SV1c', 0.5)
    
    for i in range(steps + 1):
        sv1b = i / steps
        results.append({
            'SV1a': sv1a_base,
            'SV1b': round(sv1b, 2),
            'SV1c': sv1c_base
        })
    
    return results


def sweep_sv1c(base_state: Dict[str, float], steps: int = 20) -> List[Dict]:
    """
    Sweep SV1c (cost asymmetry) across its full range while holding others constant.
    
    Useful for: Assessing sensitivity to cost advantage
    
    Args:
        base_state: Base state dictionary with SV1a, SV1b, SV1c values
        steps: Number of steps in the sweep (default 20)
    
    Returns:
        List of state dictionaries with varying SV1c values
    """
    results = []
    sv1a_base = base_state.get('SV1a', 0.5)
    sv1b_base = base_state.get('SV1b', 0.5)
    
    for i in range(steps + 1):
        sv1c = i / steps
        results.append({
            'SV1a': sv1a_base,
            'SV1b': sv1b_base,
            'SV1c': round(sv1c, 2)
        })
    
    return results


def what_if_judge_hostile(base_state: Dict[str, float]) -> Dict[str, float]:
    """
    Scenario: Judge becomes hostile.
    
    Impact: Reduces procedural advantage (SV1b).
    """
    hostile_state = base_state.copy()
    hostile_state['SV1b'] = max(0.0, hostile_state['SV1b'] - 0.30)
    return hostile_state


def what_if_costs_spike(base_state: Dict[str, float]) -> Dict[str, float]:
    """
    Scenario: Legal costs spike unexpectedly.
    
    Impact: Reduces cost asymmetry (SV1c).
    """
    cost_spike_state = base_state.copy()
    cost_spike_state['SV1c'] = max(0.0, cost_spike_state['SV1c'] - 0.40)
    return cost_spike_state


def what_if_invalidity_collapses(base_state: Dict[str, float]) -> Dict[str, float]:
    """
    Scenario: Key patent/claim validity collapses.
    
    Impact: Severely reduces claim validity (SV1a).
    """
    invalidity_state = base_state.copy()
    invalidity_state['SV1a'] = max(0.0, invalidity_state['SV1a'] - 0.50)
    return invalidity_state


def what_if_evidence_breakthrough(base_state: Dict[str, float]) -> Dict[str, float]:
    """
    Scenario: Strong new evidence emerges.
    
    Impact: Increases claim validity (SV1a) and procedural advantage (SV1b).
    """
    breakthrough_state = base_state.copy()
    breakthrough_state['SV1a'] = min(1.0, breakthrough_state['SV1a'] + 0.25)
    breakthrough_state['SV1b'] = min(1.0, breakthrough_state['SV1b'] + 0.15)
    return breakthrough_state


def compare_scenarios(base_state: Dict[str, float]) -> Dict[str, Dict]:
    """
    Compare multiple what-if scenarios against baseline.
    
    Args:
        base_state: Base state dictionary
    
    Returns:
        Dictionary mapping scenario names to resulting states
    """
    return {
        'baseline': base_state.copy(),
        'judge_hostile': what_if_judge_hostile(base_state),
        'costs_spike': what_if_costs_spike(base_state),
        'invalidity_collapses': what_if_invalidity_collapses(base_state),
        'evidence_breakthrough': what_if_evidence_breakthrough(base_state)
    }