"""
Probabilistic extensions for Procedural Leverage Engine.

This module provides uncertainty quantification, scenario exploration,
and Monte Carlo sampling on top of the deterministic core engine.

Critical Design Principle:
    NEVER import from /engine directly.
    Always consume via CLI JSON output or run_engine() function.
    This preserves determinism in the core engine.
"""

from typing import Dict, Any

__version__ = "2.0-skeleton"


def validate_json_output(json_output: Dict[str, Any]) -> bool:
    """
    Validate that JSON output from CLI matches expected schema.
    
    Args:
        json_output: Dictionary output from CLI --json mode
    
    Returns:
        True if valid, False otherwise
    
    Raises:
        ValueError: If schema is critically invalid
    """
    required_keys = ['inputs', 'scores', 'evaluation', 'interpretation', 'version']
    
    # Check top-level keys
    for key in required_keys:
        if key not in json_output:
            raise ValueError(f"Missing required key: {key}")
    
    # Validate nested structure
    if not isinstance(json_output.get('inputs'), dict):
        raise ValueError("'inputs' must be a dictionary")
    
    if not isinstance(json_output.get('scores'), dict):
        raise ValueError("'scores' must be a dictionary")
    
    if not isinstance(json_output.get('evaluation'), dict):
        raise ValueError("'evaluation' must be a dictionary")
    
    if not isinstance(json_output.get('interpretation'), dict):
        raise ValueError("'interpretation' must be a dictionary")
    
    if not isinstance(json_output.get('version'), str):
        raise ValueError("'version' must be a string")
    
    # Validate inputs substructure
    inputs = json_output['inputs']
    if not all(k in inputs for k in ['SV1a', 'SV1b', 'SV1c']):
        raise ValueError("'inputs' must contain SV1a, SV1b, SV1c")
    
    # Validate scores substructure
    scores = json_output['scores']
    if not all(k in scores for k in ['upls', 'tripwire']):
        raise ValueError("'scores' must contain upls, tripwire")
    
    # Validate evaluation substructure
    evaluation = json_output['evaluation']
    required_eval_keys = ['decision', 'confidence', 'tripwire_triggered']
    if not all(k in evaluation for k in required_eval_keys):
        raise ValueError(f"'evaluation' must contain {', '.join(required_eval_keys)}")
    
    return True