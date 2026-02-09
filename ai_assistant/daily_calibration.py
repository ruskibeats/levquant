"""Daily calibration driver for generating NotebookLM-ready prompts.

No external API calls by default. Generates prompts for manual copy-paste into NotebookLM.
Uses @style source-of-truth prompt injection — prompts are loaded verbatim from immutable files.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from ai_assistant.prompt_loader import (
    get_prompt_metadata,
    interpolate_prompt,
    load_calibration_prompt,
)


DEFAULT_OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


class DailyAICalibrator:
    """Driver for daily calibration prompting.

    Generates NotebookLM-ready calibration prompts using accumulated context
    and current engine state. No external LLM calls by default.
    
    Uses @style prompt injection: the prompt is loaded verbatim from a source
    file and interpolated with runtime context. The source file is immutable.
    """

    # Template version for tracking
    TEMPLATE_VERSION = "LEVQUANT_CALIBRATION_TEMPLATE_v1.0"
    PROMPT_VERSION = "v1"

    def __init__(self, llm_client: Optional[Any] = None):
        """Initialize calibrator.

        Args:
            llm_client: Optional interface to an LLM with .query(prompt: str) -> str method.
                       If None (default), build_prompt is used for manual copy-paste.
        """
        self.llm = llm_client
        # Load the source-of-truth prompt
        self._prompt_template = load_calibration_prompt(self.PROMPT_VERSION)

    def build_prompt(
        self,
        all_context: str,
        new_context: str,
        engine_snapshot: dict,
        assumptions_snapshot: dict,
    ) -> str:
        """Build a NotebookLM-ready calibration prompt.

        Uses @style prompt injection: loads the prompt from an immutable source
        file and interpolates runtime variables only.

        Args:
            all_context: Concatenated string of all prior journal entries.
            new_context: The new context added today.
            engine_snapshot: Current deterministic engine output.
            assumptions_snapshot: Assumptions dict from monetary corridor module.

        Returns:
            Full prompt string ready for NotebookLM.
        """
        return interpolate_prompt(
            prompt_template=self._prompt_template,
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            new_context=new_context,
            all_context=all_context,
        )

    def run(
        self,
        new_context: str,
        all_context: str,
        engine_snapshot: dict,
        assumptions_snapshot: dict,
    ) -> dict:
        """Run the calibration workflow.

        If llm_client is provided, queries the LLM. Otherwise returns the prompt
        for manual use.

        Args:
            new_context: The new context added today.
            all_context: All prior accumulated context.
            engine_snapshot: Current engine state.
            assumptions_snapshot: Current assumptions.

        Returns:
            Dictionary with calibration results and/or prompt.
        """
        prompt = self.build_prompt(
            all_context=all_context,
            new_context=new_context,
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
        )

        # Get prompt metadata for auditing
        prompt_meta = get_prompt_metadata(self.PROMPT_VERSION)

        result = {
            "date": datetime.now(UTC).isoformat(),
            "new_context": new_context,
            "raw_prompt": prompt,
            "prompt_metadata": prompt_meta,
            "template_version": self.TEMPLATE_VERSION,
            "llm_response_json": None,
            "delta_summary": None,
        }

        if self.llm is not None:
            try:
                llm_output = self.llm.query(prompt)
                parsed = parse_llm_output(llm_output)
                result["llm_response_json"] = parsed
                result["delta_summary"] = self._extract_delta_summary(parsed)
            except Exception as e:
                result["llm_error"] = str(e)

        return result

    def _extract_delta_summary(self, parsed: dict) -> dict:
        """Extract a concise delta summary from parsed LLM output."""
        return {
            "drift_score": parsed.get("drift_detection", {}).get("drift_score", 0),
            "corridor_alignment": parsed.get("settlement_corridor_check", {}).get("corridor_alignment", "unknown"),
            "key_action": parsed.get("daily_actions", {}).get("what_to_update_in_inputs", [])[:1],
            "watch_next": parsed.get("daily_actions", {}).get("what_to_watch_next", [])[:2],
        }


def parse_llm_output(output: str) -> dict:
    """Safe JSON parse with fallback reporting.

    Args:
        output: Raw string output from LLM.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If output cannot be parsed as JSON.
    """
    # Try to extract JSON from markdown code blocks if present
    cleaned = output.strip()

    # Remove markdown code block markers if present
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output is not valid JSON: {e}\nOutput preview: {cleaned[:500]}")


def validate_calibration_output(output: dict) -> tuple[bool, list[str]]:
    """Validate calibration output against required schema.
    
    Args:
        output: Parsed JSON output from LLM.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required top-level keys
    required_keys = [
        "timestamp_utc",
        "model_version",
        "engine_snapshot",
        "fact_checks",
        "drift_detection",
        "tripwire_calibration",
        "settlement_corridor_check",
        "daily_actions",
    ]
    
    for key in required_keys:
        if key not in output:
            errors.append(f"Missing required key: {key}")
    
    # Check model version matches
    if output.get("model_version") != "LEVQUANT_CALIBRATION_TEMPLATE_v1.0":
        errors.append(f"Unexpected model_version: {output.get('model_version')}")
    
    # Check for narrative content (simple heuristic)
    output_str = json.dumps(output)
    narrative_indicators = ["I think", "In my opinion", "I believe", "should", "recommend"]
    for indicator in narrative_indicators:
        if indicator in output_str:
            errors.append(f"Possible narrative content detected: '{indicator}'")
    
    return len(errors) == 0, errors


def save_daily_report(report: dict, outputs_dir: Optional[Path] = None) -> Path:
    """Save the daily calibration report with timestamp naming.

    Args:
        report: Dictionary containing calibration results.
        outputs_dir: Directory to save report. Defaults to outputs/.

    Returns:
        Path to saved JSON file.
    """
    out_dir = outputs_dir or DEFAULT_OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    filename = f"daily_ai_{timestamp}.json"
    filepath = out_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return filepath


def export_prompt_markdown(prompt: str, outputs_dir: Optional[Path] = None) -> Path:
    """Export the prompt to a Markdown file for easy copy-paste.

    Args:
        prompt: The calibration prompt string.
        outputs_dir: Directory to save file. Defaults to outputs/.

    Returns:
        Path to saved Markdown file.
    """
    out_dir = outputs_dir or DEFAULT_OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    filename = f"daily_prompt_{timestamp}.md"
    filepath = out_dir / filename

    filepath.write_text(prompt, encoding="utf-8")
    return filepath
