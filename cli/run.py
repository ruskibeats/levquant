"""
Command-line entry point for the Procedural Leverage Engine.

One command, one output.
Loads state, computes scores, prints summary, exits.

No loops. No menus. No interactivity.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.state import get_current_state
from engine.scoring import calculate_comprehensive_score
from engine.evaluation import get_risk_assessment
from engine.interpretation import format_summary


def main():
    """
    Main execution function.
    
    1. Load current state
    2. Compute scores
    3. Print clean summary
    4. Exit
    """
    try:
        # Step 1: Load current state
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
        
        # Step 4: Print clean summary
        summary = format_summary(state, scores, risk_assessment)
        print(summary)
        
        # Exit cleanly
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())