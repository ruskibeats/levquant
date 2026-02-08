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

from ai_assistant.context_journal import add_context, get_all_context
from ai_assistant.daily_calibration import DailyAICalibrator, export_prompt_markdown, save_daily_report
from ai_assistant.calibration_probe import run_calibration_probe
from engine.state import get_current_state, load_state
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


def cmd_calibrate(args) -> int:
    """Execute the calibrate command: run LLM Calibration Probe."""
    from decision_support.monetary import ASSUMPTIONS
    from ai_assistant.calibration_probe import get_probe_history
    
    # Show history if requested
    if args.history:
        history = get_probe_history(limit=10)
        if not history:
            print("No calibration probe history found.")
            return 0
        print("Calibration Probe History (last 10):")
        print("-" * 60)
        for entry in history:
            print(f"  {entry.get('timestamp_utc', 'N/A')}")
            print(f"    Status: {entry.get('status', 'N/A')}")
            if 'fact_certainty_index' in entry:
                print(f"    Fact Certainty: {entry['fact_certainty_index']:.2f}")
                print(f"    Drift Alert: {entry.get('drift_alert', 'N/A')}")
                print(f"    Settlement Range: {entry.get('recommended_settlement_range_gbp', 'N/A')}")
            print()
        return 0
    
    try:
        # Get engine snapshot
        engine_result = run_engine(state={
            "SV1a": args.sv1a,
            "SV1b": args.sv1b,
            "SV1c": args.sv1c,
        })
        
        # Build assumptions snapshot
        assumptions_snapshot = {
            **ASSUMPTIONS,
            "current_posture": "NORMAL",
            "fear_index": 0.0,
            "kill_switches_active": [],
        }
        
        # Run calibration probe (no LLM client = prompt only mode)
        result = run_calibration_probe(
            engine_snapshot=engine_result,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=None,  # Prompt only for now
        )
        
        # Print prompt if requested
        if args.print_prompt:
            print("=" * 60)
            print("LLM CALIBRATION PROBE PROMPT")
            print("=" * 60)
            print(result["prompt"])
            print("=" * 60)
        
        # Print summary
        print(f"✓ Calibration probe generated")
        print(f"  Timestamp: {result['timestamp_utc']}")
        print(f"  Status: {result['status']}")
        print(f"  Output saved to: outputs/calibration/")
        
        if not args.print_prompt:
            print(f"\nTo see the prompt, run with --print-prompt")
            print(f"To run with an LLM, provide an llm_client to run_calibration_probe()")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def cmd_daily_ai(args) -> int:
    """Execute the daily-ai command: save context and generate calibration prompt."""
    # Import here to avoid circular import at module load time
    from decision_support.monetary import ASSUMPTIONS

    try:
        # Add new context to journal
        add_context(
            doc_text=args.text,
            entry_type=args.entry_type,
            source="cli",
        )
        print(f"✓ Context saved to journal (type: {args.entry_type})")

        # Get all context (with optional limit)
        all_context = get_all_context(limit=args.limit if args.limit > 0 else None)

        # Get engine snapshot with current SV values
        engine_result = run_engine(state={
            "SV1a": args.sv1a,
            "SV1b": args.sv1b,
            "SV1c": args.sv1c,
        })

        # Build assumptions snapshot
        assumptions_snapshot = {
            **ASSUMPTIONS,
            "current_posture": "NORMAL",  # Default; CLI uses simplified posture
            "fear_index": 0.0,
            "kill_switches_active": [],
        }

        # Build and run calibration
        calibrator = DailyAICalibrator(llm_client=None)
        result = calibrator.run(
            new_context=args.text,
            all_context=all_context,
            engine_snapshot=engine_result,
            assumptions_snapshot=assumptions_snapshot,
        )

        # Save report
        outputs_dir = Path(__file__).parent.parent / "outputs"
        report_path = save_daily_report(result, outputs_dir=outputs_dir)
        print(f"✓ Report saved: {report_path}")

        # Optionally export prompt as markdown
        if args.export_md:
            md_path = export_prompt_markdown(result["raw_prompt"], outputs_dir=outputs_dir)
            print(f"✓ Prompt exported: {md_path}")

        # Print prompt to stdout
        if args.print_prompt:
            print("\n" + "=" * 60)
            print("GENERATED NOTEBOOKLM PROMPT")
            print("=" * 60)
            print(result["raw_prompt"])
            print("=" * 60)

        # Print summary
        print("\nCalibration Summary:")
        print(f"  Date: {result['date']}")
        print(f"  New context length: {len(args.text)} chars")
        print(f"  Total context entries: {len(all_context.split('---')) if all_context else 0}")
        print(f"  Engine UPLS: {engine_result['scores']['upls']:.3f}")
        print(f"  Engine Tripwire: {engine_result['scores']['tripwire']:.2f}")

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


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
  python -m cli.run                    # Run engine (default)
  python -m cli.run --json             # Machine-readable JSON output
  python -m cli.run daily-ai --text "New email from HMRC..."

Commands:
  (no command)    Run the leverage engine
  daily-ai        Save context and generate NotebookLM calibration prompt

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
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # calibrate subcommand (NEW)
    calibrate_parser = subparsers.add_parser(
        'calibrate',
        help='Run LLM Calibration Probe for independent assessment',
        description='Run an external LLM calibration probe to detect drift, overconfidence, and assumption inflation.'
    )
    calibrate_parser.add_argument(
        '--sv1a',
        type=float,
        default=0.5,
        help='SV1a value (Right to Bring the Claim) for engine snapshot (default: 0.5)'
    )
    calibrate_parser.add_argument(
        '--sv1b',
        type=float,
        default=0.5,
        help='SV1b value (Rule-Breaking Leverage) for engine snapshot (default: 0.5)'
    )
    calibrate_parser.add_argument(
        '--sv1c',
        type=float,
        default=0.5,
        help='SV1c value (Cost Pressure on Them) for engine snapshot (default: 0.5)'
    )
    calibrate_parser.add_argument(
        '--print-prompt', '-p',
        action='store_true',
        help='Print calibration probe prompt to stdout (no LLM call)'
    )
    calibrate_parser.add_argument(
        '--history',
        action='store_true',
        help='Show calibration probe history'
    )
    
    # daily-ai subcommand
    daily_ai_parser = subparsers.add_parser(
        'daily-ai',
        help='Save context and generate NotebookLM calibration prompt',
        description='Add new context to the journal and generate a calibration prompt for NotebookLM.'
    )
    daily_ai_parser.add_argument(
        '--text', '-t',
        required=True,
        help='New context text to add (e.g., email content, court note)'
    )
    daily_ai_parser.add_argument(
        '--entry-type', '-e',
        default='text',
        choices=['text', 'email', 'court_note', 'phone_call', 'other'],
        help='Type of context entry (default: text)'
    )
    daily_ai_parser.add_argument(
        '--sv1a',
        type=float,
        default=0.5,
        help='SV1a value (Right to Bring the Claim) for engine snapshot (default: 0.5)'
    )
    daily_ai_parser.add_argument(
        '--sv1b',
        type=float,
        default=0.5,
        help='SV1b value (Rule-Breaking Leverage) for engine snapshot (default: 0.5)'
    )
    daily_ai_parser.add_argument(
        '--sv1c',
        type=float,
        default=0.5,
        help='SV1c value (Cost Pressure on Them) for engine snapshot (default: 0.5)'
    )
    daily_ai_parser.add_argument(
        '--limit', '-l',
        type=int,
        default=0,
        help='Limit context entries (0 = all, default: 0)'
    )
    daily_ai_parser.add_argument(
        '--export-md', '-m',
        action='store_true',
        help='Also export prompt as Markdown file'
    )
    daily_ai_parser.add_argument(
        '--print-prompt', '-p',
        action='store_true',
        help='Print generated prompt to stdout'
    )
    
    args = parser.parse_args(argv)
    
    # Route to appropriate command
    if args.command == 'daily-ai':
        return cmd_daily_ai(args)
    
    if args.command == 'calibrate':
        return cmd_calibrate(args)
    
    # Default: run engine
    try:
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