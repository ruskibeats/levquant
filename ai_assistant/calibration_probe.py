"""LLM Calibration Probe - Independent external assessment system.

Deterministic, repeatable, auditable calibration checks.
No engine modifications. No advocacy or optimisation.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from ai_assistant.context_journal import get_all_context

# Fixed calibration probe prompt template (verbatim)
CALIBRATION_PROBE_PROMPT = """### 🔧 LLM CALIBRATION PROBE
(Machine-only · deterministic · repeatable)

System instruction:
You are acting as a calibration auditor.
You must not advocate, persuade, or optimise outcomes.
Your task is to detect drift, overconfidence, and assumption inflation.
All answers must be probabilistic, bounded, and evidence-referenced.

You are examining a procedural leverage assessment system (LEVQUANT).
Your job is to independently assess whether the system's outputs are well-calibrated.

---

## INPUT DATA

### 1. Engine Snapshot (Deterministic Core)
```json
{engine_snapshot}
```

### 2. Assumptions Snapshot (Pricing Layer)
```json
{assumptions_snapshot}
```

### 3. Accumulated Context (Journal Entries)
{journal_context}

---

## CALIBRATION QUESTIONS

Answer each with a probability (0.0–1.0) and brief evidence reference.

### Section 1: Fact Certainty Assessment
1. What is the probability that the key factual claims are accurate? (fact_certainty_index)
2. Which facts have the weakest evidentiary support?
3. Are any facts classified as "realised" that should be "prospective"?

### Section 2: Procedural Risk Assessment
4. What is the probability of adverse procedural outcome? (procedural_risk_index)
5. Are there unaddressed procedural vulnerabilities?
6. Is the timeline risk properly calibrated?

### Section 3: Counterparty Stress Analysis
7. What is the probability of insurer exit/void? (insurer_exit_probability)
8. What is the law firm breakpoint score (0–100)? (law_firm_breakpoint_score)
9. Which party is most likely to break first under pressure?

### Section 4: Settlement Range Sanity Check
10. Given the above, what is the reasonable settlement range in GBP? (recommended_settlement_range_gbp)
11. Does this range differ materially from the system's output?
12. If so, what explains the divergence?

### Section 5: Drift Detection
13. Are there signs of assumption inflation? (drift_alert: true/false)
14. Has confidence increased without new evidence?
15. Are there anchoring effects from the £15m/£9m objectives?

---

## OUTPUT FORMAT (JSON ONLY)

You must output ONLY valid JSON. No markdown, no commentary.

Required structure:
```json
{{
  "probe_version": "1.0",
  "timestamp_utc": "ISO8601",
  "fact_certainty_index": 0.0,
  "procedural_risk_index": 0.0,
  "insurer_exit_probability": 0.0,
  "law_firm_breakpoint_score": 0,
  "recommended_settlement_range_gbp": "£X–£Y",
  "drift_alert": false,
  "section_1_facts": {{
    "fact_certainty_index": 0.0,
    "weakest_facts": ["..."],
    "misclassified_facts": ["..."]
  }},
  "section_2_procedural": {{
    "procedural_risk_index": 0.0,
    "vulnerabilities": ["..."],
    "timeline_risk": "..."
  }},
  "section_3_counterparty": {{
    "insurer_exit_probability": 0.0,
    "law_firm_breakpoint_score": 0,
    "first_to_break": "..."
  }},
  "section_4_settlement": {{
    "recommended_range": "£X–£Y",
    "system_comparison": "...",
    "divergence_explanation": "..."
  }},
  "section_5_drift": {{
    "drift_alert": false,
    "assumption_inflation": ["..."],
    "anchoring_effects": "..."
  }},
  "overall_assessment": "One-paragraph summary of calibration status"
}}
```

⚠️ FAILURE CONDITIONS:
- If you output markdown → FAIL
- If you add commentary → FAIL
- If you omit required keys → FAIL
- If you advocate for outcomes → FAIL
- If you optimise for user objectives → FAIL

Your role is calibration auditor, not advocate.
"""

DEFAULT_OUTPUT_DIR = Path("outputs/calibration")
LOG_FILE = Path("logs/calibration.log")

REQUIRED_KEYS = [
    "probe_version",
    "timestamp_utc",
    "fact_certainty_index",
    "procedural_risk_index",
    "insurer_exit_probability",
    "law_firm_breakpoint_score",
    "recommended_settlement_range_gbp",
    "drift_alert",
]


def run_calibration_probe(
    engine_snapshot: dict,
    assumptions_snapshot: dict,
    journal_path: Optional[Path] = None,
    llm_client: Optional[Any] = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    """Run the LLM Calibration Probe and return parsed JSON output.
    
    Persists raw + parsed output to disk. Appends summary to audit log.
    
    Args:
        engine_snapshot: Current deterministic engine output
        assumptions_snapshot: Assumptions from monetary corridor module
        journal_path: Optional path to context journal
        llm_client: Optional LLM client with .query(prompt) -> str method
        output_dir: Directory for output files (default: outputs/calibration)
    
    Returns:
        Parsed calibration probe result as dictionary
    
    Raises:
        ValueError: If LLM output is invalid or missing required keys
        RuntimeError: If probe execution fails
    """
    timestamp = datetime.now(UTC)
    timestamp_str = timestamp.isoformat()
    
    # Get journal context
    journal_context = get_all_context(journal_path) if journal_path else "[No journal context provided]"
    
    # Build prompt
    prompt = CALIBRATION_PROBE_PROMPT.format(
        engine_snapshot=json.dumps(engine_snapshot, indent=2, default=str),
        assumptions_snapshot=json.dumps(assumptions_snapshot, indent=2, default=str),
        journal_context=journal_context if journal_context else "[Empty journal]",
    )
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # If no LLM client, return prompt for manual use
    if llm_client is None:
        result = {
            "probe_version": "1.0",
            "timestamp_utc": timestamp_str,
            "status": "prompt_only",
            "prompt": prompt,
            "parsed_output": None,
            "error": None,
        }
        _persist_output(result, output_dir, timestamp_str, prompt_only=True)
        return result
    
    try:
        # Call LLM
        raw_output = llm_client.query(prompt)
        
        # Parse and validate
        parsed = _parse_probe_output(raw_output)
        
        # Validate required keys
        _validate_probe_output(parsed)
        
        # Build result
        result = {
            "probe_version": "1.0",
            "timestamp_utc": timestamp_str,
            "status": "completed",
            "prompt": prompt,
            "raw_output": raw_output,
            "parsed_output": parsed,
            "error": None,
        }
        
        # Persist
        _persist_output(result, output_dir, timestamp_str, prompt_only=False)
        _append_to_log(result)
        
        return result
        
    except Exception as e:
        # Log failure
        result = {
            "probe_version": "1.0",
            "timestamp_utc": timestamp_str,
            "status": "failed",
            "prompt": prompt,
            "raw_output": raw_output if 'raw_output' in locals() else None,
            "parsed_output": None,
            "error": str(e),
        }
        _persist_output(result, output_dir, timestamp_str, prompt_only=False)
        _append_to_log(result)
        raise RuntimeError(f"Calibration probe failed: {e}") from e


def _parse_probe_output(output: str) -> dict:
    """Parse LLM output, extracting JSON from markdown if necessary.
    
    Args:
        output: Raw string from LLM
    
    Returns:
        Parsed dictionary
    
    Raises:
        ValueError: If output cannot be parsed as JSON
    """
    cleaned = output.strip()
    
    # Remove markdown code blocks if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    # Check for non-JSON content
    if not cleaned.startswith("{"):
        raise ValueError(f"Output does not start with '{{'. Possible markdown or commentary detected.")
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e


def _validate_probe_output(parsed: dict) -> None:
    """Validate that parsed output contains all required keys.
    
    Args:
        parsed: Parsed dictionary
    
    Raises:
        ValueError: If required keys are missing
    """
    missing = [key for key in REQUIRED_KEYS if key not in parsed]
    if missing:
        raise ValueError(f"Missing required keys: {missing}")
    
    # Validate types
    if not isinstance(parsed.get("drift_alert"), bool):
        raise ValueError("drift_alert must be boolean")
    
    for key in ["fact_certainty_index", "procedural_risk_index", "insurer_exit_probability"]:
        value = parsed.get(key)
        if not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be numeric")
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{key} must be between 0.0 and 1.0")
    
    score = parsed.get("law_firm_breakpoint_score")
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("law_firm_breakpoint_score must be integer 0–100")


def _persist_output(
    result: dict,
    output_dir: Path,
    timestamp_str: str,
    prompt_only: bool = False,
) -> Path:
    """Persist probe result to disk.
    
    Args:
        result: Result dictionary
        output_dir: Output directory
        timestamp_str: ISO timestamp string
        prompt_only: Whether this is a prompt-only result
    
    Returns:
        Path to saved file
    """
    filename = f"calibration_{timestamp_str.replace(':', '').replace('-', '').replace('.', '')}.json"
    filepath = output_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    return filepath


def _append_to_log(result: dict) -> None:
    """Append summary to audit log (JSONL format).
    
    Args:
        result: Result dictionary
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Create summary for log
    summary = {
        "timestamp_utc": result.get("timestamp_utc"),
        "status": result.get("status"),
        "probe_version": result.get("probe_version"),
    }
    
    # Add parsed output summary if available
    parsed = result.get("parsed_output")
    if parsed:
        summary.update({
            "fact_certainty_index": parsed.get("fact_certainty_index"),
            "procedural_risk_index": parsed.get("procedural_risk_index"),
            "insurer_exit_probability": parsed.get("insurer_exit_probability"),
            "law_firm_breakpoint_score": parsed.get("law_firm_breakpoint_score"),
            "recommended_settlement_range_gbp": parsed.get("recommended_settlement_range_gbp"),
            "drift_alert": parsed.get("drift_alert"),
        })
    
    if result.get("error"):
        summary["error"] = result["error"]
    
    # Append to log (JSONL)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


def get_probe_history(limit: Optional[int] = None) -> list[dict]:
    """Read calibration probe history from audit log.
    
    Args:
        limit: Optional maximum number of entries to return
    
    Returns:
        List of probe summary dictionaries
    """
    if not LOG_FILE.exists():
        return []
    
    entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    if limit:
        entries = entries[-limit:]
    
    return entries


def compare_probes(timestamp_a: str, timestamp_b: str) -> dict:
    """Compare two calibration probe results.
    
    Args:
        timestamp_a: First probe timestamp
        timestamp_b: Second probe timestamp
    
    Returns:
        Comparison dictionary with deltas
    """
    # This is a placeholder for future implementation
    # Would need to load full probe results from output files
    return {
        "timestamp_a": timestamp_a,
        "timestamp_b": timestamp_b,
        "comparison_status": "not_implemented",
        "note": "Load probe results from outputs/calibration/ and compare",
    }
