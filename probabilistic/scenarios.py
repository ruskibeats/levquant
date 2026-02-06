"""
Named scenarios for probabilistic extensions.

This file provides predefined stress tests and what-if scenarios.
It does not import from /engine.

Critical Design Principle:
    Use probabilistic.adapters.run_deterministic_engine() to get results.
    Never import from /engine directly.

Status: v2.0-skeleton (structure only, not implemented)
"""

from typing import Dict, List
from probabilistic.adapters import run_deterministic_engine
from probabilistic.schemas import ScenarioResult


# Predefined scenarios
SCENARIOS = {
    'cost_spike': {
        'description': 'Maximum cost asymmetry - worst-case cost exposure',
        'state': {'SV1a': 0.38, 'SV1b': 0.86, 'SV1c': 1.0}  # SV1c maxed
    },
    
    'invalidity_collapse': {
        'description': 'Minimum claim validity - case collapses',
        'state': {'SV1a': 0.1, 'SV1b': 0.86, 'SV1c': 0.75}  # SV1a minimized
    },
    
    'procedural_loss': {
        'description': 'Minimum procedural advantage - lost procedural edge',
        'state': {'SV1a': 0.38, 'SV1b': 0.1, 'SV1c': 0.75}  # SV1b minimized
    },
    
    'perfect_case': {
        'description': 'All factors maximized - ideal scenario',
        'state': {'SV1a': 1.0, 'SV1b': 1.0, 'SV1c': 1.0}  # All maxed
    },
    
    'worst_case': {
        'description': 'All factors minimized - catastrophic scenario',
        'state': {'SV1a': 0.0, 'SV1b': 0.0, 'SV1c': 0.0}  # All minimized
    },
    
    'judge_hostile': {
        'description': 'Procedural advantage reduced (simulating hostile judge)',
        'state': {'SV1a': 0.38, 'SV1b': 0.5, 'SV1c': 0.75}  # SV1b reduced to 0.5
    },
    
    'cost_neutral': {
        'description': 'Cost asymmetry neutral - balanced cost exposure',
        'state': {'SV1a': 0.38, 'SV1b': 0.86, 'SV1c': 0.5}  # SV1c at 0.5
    },
    
    'claim_moderate': {
        'description': 'Claim validity moderate - balanced strength',
        'state': {'SV1a': 0.5, 'SV1b': 0.86, 'SV1c': 0.75}  # SV1a at 0.5
    }
}


def run_scenario(scenario_name: str) -> ScenarioResult:
    """
    Run a predefined scenario by name.
    
    Args:
        scenario_name: Name of scenario from SCENARIOS dict
    
    Returns:
        ScenarioResult with deterministic engine output
    
    Raises:
        ValueError: If scenario_name is not found
    
    Example:
        >>> result = run_scenario('cost_spike')
        >>> print(result.scenario_name)
        'cost_spike'
        >>> print(result.evaluation.decision)
        'HOLD'
    """
    if scenario_name not in SCENARIOS:
        available = ', '.join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {available}")
    
    scenario_data = SCENARIOS[scenario_name]
    state = scenario_data['state']
    description = scenario_data['description']
    
    # Run deterministic engine
    deterministic_output = run_deterministic_engine(state=state)
    
    return ScenarioResult(
        scenario_name=scenario_name,
        description=description,
        output=deterministic_output
    )


def run_all_scenarios() -> List[ScenarioResult]:
    """
    Run all predefined scenarios.
    
    Returns:
        List of ScenarioResult objects, one for each predefined scenario
    
    Example:
        >>> results = run_all_scenarios()
        >>> len(results)
        8
    """
    results = []
    for scenario_name in SCENARIOS.keys():
        result = run_scenario(scenario_name)
        results.append(result)
    
    return results


def run_custom_scenario(
    scenario_name: str,
    sv1a: float,
    sv1b: float,
    sv1c: float,
    description: str
) -> ScenarioResult:
    """
    Run a custom scenario with specified SV values.
    
    Args:
        scenario_name: Name for this custom scenario
        sv1a: SV1a value [0.0, 1.0]
        sv1b: SV1b value [0.0, 1.0]
        sv1c: SV1c value [0.0, 1.0]
        description: Human-readable description of scenario
    
    Returns:
        ScenarioResult with deterministic engine output
    
    Raises:
        ValueError: If any SV value is out of [0.0, 1.0] range
    
    Example:
        >>> result = run_custom_scenario(
        ...     scenario_name='mixed_case',
        ...     sv1a=0.6,
        ...     sv1b=0.4,
        ...     sv1c=0.8,
        ...     description='Mixed signals'
        ... )
        >>> print(result.evaluation.decision)
        'HOLD'
    """
    # Validate inputs
    for name, value in [('SV1a', sv1a), ('SV1b', sv1b), ('SV1c', sv1c)]:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0.0, 1.0], got {value}")
    
    # Create state
    state = {'SV1a': sv1a, 'SV1b': sv1b, 'SV1c': sv1c}
    
    # Run deterministic engine
    deterministic_output = run_deterministic_engine(state=state)
    
    return ScenarioResult(
        scenario_name=scenario_name,
        description=description,
        output=deterministic_output
    )


def list_scenarios() -> List[str]:
    """
    List all available predefined scenario names.
    
    Returns:
        List of scenario names
    
    Example:
        >>> names = list_scenarios()
        >>> print(names)
        ['cost_spike', 'invalidity_collapse', 'procedural_loss', ...]
    """
    return list(SCENARIOS.keys())


def get_scenario_description(scenario_name: str) -> str:
    """
    Get description for a predefined scenario.
    
    Args:
        scenario_name: Name of scenario
    
    Returns:
        Description string
    
    Raises:
        ValueError: If scenario_name is not found
    
    Example:
        >>> desc = get_scenario_description('cost_spike')
        >>> print(desc)
        'Maximum cost asymmetry - worst-case cost exposure'
    """
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    
    return SCENARIOS[scenario_name]['description']