"""
Command-line entry point for the Procedural Leverage Engine.

CLI Contract:
- One command, one output
- Loads state, computes scores, prints summary, exits
- No loops, menus, or interactivity
- Supports human-readable (default) and JSON (--json) output modes

Exit Codes:
- 0: Success
- 1: Unexpected error
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.state import get_current_state
from engine.scoring import calculate_comprehensive_score
from engine.evaluation import get_risk_assessment
from engine.interpretation import format_summary, get_full_interpretation


VERSION = "1.0"


def run_engine(state: Optional[Dict] = None) -> Dict:
    """
    Core engine logic - testable without CLI layer.
    
    Args:
        state: Optional state dictionary. If None, uses current state from engine/state.py
    
    Returns:
        Complete result dictionary with inputs, scores, evaluation, and interpretation
    """
    # Step 1: Load or validate state
    if state is None:
        state = get_current_state()
    
    # Step 2: Compute scores
    sv1a = state['SV1a']
    sv1b = state['SV1b']
    sv1c = state['SV1c']
    
    scores = calculate_comprehensive_score(sv1a, sv1b, sv1c)
    
    # Step 3: Get risk assessment
    risk_assessment = get_risk_assessment(
        scores['upls'],
        scores['tripwire']
    )
    
    # Step 4: Get interpretation
    interpretation = get_full_interpretation(
        scores['upls'],
        scores['tripwire'],
        risk_assessment['decision'],
        risk_assessment['confidence']
    )
    
    return {
        'inputs': state,
        'scores': scores,
        'evaluation': risk_assessment,
        'interpretation': interpretation,
        'version': VERSION
    }


def main(argv: Optional[list] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        argv: Optional argument list (for testing). If None, uses sys.argv.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    if argv is None:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        description='Procedural Leverage Engine - Commercial dispute settlement decision support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.run              # Human-readable output (default)
  python -m cli.run --json       # Machine-readable JSON output
  python -m cli.run -j           # Short form for JSON mode

Output Schema (JSON mode):
  {
    "inputs": {"SV1a": 0.38, "SV1b": 0.86, "SV1c": 0.75},
    "scores": {"upls": 0.641, "tripwire": 6.41},
    "evaluation": {"decision": "HOLD", "confidence": "Moderate", "tripwire_triggered": false},
    "interpretation": {"leverage_position": "...", "decision_explanation": "...", "tripwire_status": "...", "confidence_explanation": "..."},
    "version": "1.0"
  }
        """
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output in JSON format (machine-readable)'
    )
    
    args = parser.parse_args(argv)
    
    try:
        # Run engine
        result = run_engine()
        
        # Output
        if args.json:
            # JSON mode: machine-readable output
            json_output = json.dumps(result, indent=2)
            print(json_output)
        else:
            # Human-readable mode: formatted summary
            summary = format_summary(
                result['inputs'],
                result['scores'],
                result['evaluation']
            )
            print(summary)
        
        # Exit cleanly
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())