"""
CLI adapter for probabilistic extensions.

This file provides a Python interface to the deterministic engine by
wrapping the CLI JSON output. It does not import from /engine.

Critical Design Principle:
    Call CLI subprocess or use run_engine() from CLI layer.
    Never import from /engine directly.
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for CLI import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli.run import run_engine as cli_run_engine
from probabilistic.schemas import DeterministicOutput


def run_deterministic_engine(
    state: Optional[Dict[str, float]] = None,
    use_cli: bool = False
) -> DeterministicOutput:
    """
    Run deterministic engine and return structured output.
    
    This function can use either:
    1. Direct Python call to cli.run.run_engine() (default, faster)
    2. Subprocess call to CLI JSON output (use_cli=True, safer boundary)
    
    Args:
        state: Optional state dictionary. If None, uses current state from engine/state.py
        use_cli: If True, uses subprocess call to CLI. If False, uses direct Python call.
    
    Returns:
        DeterministicOutput: Validated structured output
    
    Raises:
        ValueError: If engine output is invalid
        RuntimeError: If CLI subprocess fails (when use_cli=True)
    
    Example:
        >>> result = run_deterministic_engine()
        >>> print(result.evaluation.decision)
        'HOLD'
        >>> print(result.scores.upls)
        0.641
    """
    if use_cli:
        # Use subprocess call (safest boundary)
        result = _run_via_subprocess()
    else:
        # Use direct Python call (faster, still clean boundary)
        result_dict = cli_run_engine(state=state)
        result = DeterministicOutput(**result_dict)
    
    return result


def run_deterministic_engine_json(
    state: Optional[Dict[str, float]] = None,
    use_cli: bool = False
) -> Dict:
    """
    Run deterministic engine and return raw dictionary.
    
    This is a convenience function for when you don't need Pydantic validation.
    
    Args:
        state: Optional state dictionary. If None, uses current state from engine/state.py
        use_cli: If True, uses subprocess call to CLI. If False, uses direct Python call.
    
    Returns:
        Dictionary output from deterministic engine
    """
    if use_cli:
        return _run_via_subprocess()
    else:
        return cli_run_engine(state=state)


def _run_via_subprocess() -> Dict:
    """
    Run deterministic engine via subprocess CLI call.
    
    This is the safest boundary option because it uses a separate process.
    Useful for testing and isolation.
    
    Returns:
        Dictionary output from deterministic engine
    
    Raises:
        RuntimeError: If subprocess fails or returns invalid JSON
    """
    # Get CLI script path
    cli_script = project_root / 'cli' / 'run.py'
    
    # Run subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'cli.run', '--json'],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        check=False  # Don't raise CalledProcessError, handle manually
    )
    
    # Check for errors
    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        raise RuntimeError(f"CLI subprocess failed with code {result.returncode}: {error_msg}")
    
    # Parse JSON output
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"CLI returned invalid JSON: {e}")
    
    # Validate basic structure
    required_keys = ['inputs', 'scores', 'evaluation', 'interpretation', 'version']
    for key in required_keys:
        if key not in output:
            raise RuntimeError(f"CLI output missing required key: {key}")
    
    return output


def batch_run(
    states: list[Dict[str, float]],
    use_cli: bool = False
) -> list[DeterministicOutput]:
    """
    Run deterministic engine for multiple states.
    
    This is useful for Monte Carlo sampling and scenario sweeps.
    
    Args:
        states: List of state dictionaries
        use_cli: If True, uses subprocess call for each state. If False, uses direct Python call.
    
    Returns:
        List of DeterministicOutput objects
    
    Example:
        >>> states = [
        ...     {'SV1a': 0.38, 'SV1b': 0.86, 'SV1c': 0.75},
        ...     {'SV1a': 0.90, 'SV1b': 0.95, 'SV1c': 0.80}
        ... ]
        >>> results = batch_run(states)
        >>> len(results)
        2
    """
    results = []
    for state in states:
        result = run_deterministic_engine(state=state, use_cli=use_cli)
        results.append(result)
    return results