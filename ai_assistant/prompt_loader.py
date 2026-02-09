"""Prompt loader for @style source-of-truth calibration prompts.

Loads calibration prompts from immutable source files.
No trimming, no templating, no interpolation — verbatim injection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


# Source of truth prompt files
PROMPTS_DIR: Final[Path] = Path(__file__).parent / "prompts"

CALIBRATION_PROMPT_V1: Final[str] = "LEVQUANT_CALIBRATION_OUTPUT_PROMPT_v1.txt"


def load_calibration_prompt(version: str = "v1") -> str:
    """Load the calibration prompt by reference (@style semantics).
    
    Args:
        version: Prompt version to load. Currently only "v1" is supported.
        
    Returns:
        Full prompt text loaded verbatim from source file.
        
    Raises:
        FileNotFoundError: If prompt file is missing.
        ValueError: If version is not supported.
        
    Guarantees:
        - No token shortening
        - No accidental edits
        - Full prompt always used
    """
    if version != "v1":
        raise ValueError(f"Unsupported prompt version: {version}. Only 'v1' is supported.")
    
    prompt_path = PROMPTS_DIR / CALIBRATION_PROMPT_V1
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Calibration prompt not found: {prompt_path}\n"
            f"Ensure {CALIBRATION_PROMPT_V1} exists in {PROMPTS_DIR}"
        )
    
    # Load verbatim — no modifications
    return prompt_path.read_text(encoding="utf-8")


def get_prompt_metadata(version: str = "v1") -> dict:
    """Get metadata about the loaded prompt.
    
    Args:
        version: Prompt version.
        
    Returns:
        Dictionary with prompt metadata for auditing.
    """
    prompt_path = PROMPTS_DIR / CALIBRATION_PROMPT_V1
    prompt_text = load_calibration_prompt(version)
    
    return {
        "version": version,
        "filename": CALIBRATION_PROMPT_V1,
        "path": str(prompt_path),
        "size_bytes": len(prompt_text.encode("utf-8")),
        "size_chars": len(prompt_text),
        "line_count": len(prompt_text.splitlines()),
        "template_tag": "LEVQUANT_CALIBRATION_TEMPLATE_v1.0",
    }


def interpolate_prompt(
    prompt_template: str,
    engine_snapshot: dict,
    assumptions_snapshot: dict,
    new_context: str,
    all_context: str,
) -> str:
    """Interpolate variables into the prompt template.
    
    This is the ONLY place where template substitution happens.
    The source prompt file itself is never modified.
    
    Args:
        prompt_template: The raw prompt template from load_calibration_prompt().
        engine_snapshot: Current deterministic engine output.
        assumptions_snapshot: Assumptions dict from monetary corridor module.
        new_context: The new context added today.
        all_context: All prior accumulated context.
        
    Returns:
        Interpolated prompt ready for LLM consumption.
    """
    import json
    
    # Format engine snapshot as JSON
    engine_json = json.dumps(engine_snapshot, indent=2)
    assumptions_json = json.dumps(assumptions_snapshot, indent=2)
    
    # Get pressure level for specific interpolation
    scores = engine_snapshot.get("scores", {})
    pressure_level = scores.get("tripwire", 0)
    
    # Handle empty contexts
    new_context_display = new_context.strip() if new_context.strip() else "[No new context added today]"
    all_context_display = all_context.strip() if all_context.strip() else "[No prior context in journal]"
    
    # Substitute placeholders
    result = prompt_template
    result = result.replace("{{ENGINE_SNAPSHOT}}", f"```json\n{engine_json}\n```")
    result = result.replace("{{ASSUMPTIONS_SNAPSHOT}}", f"```json\n{assumptions_json}\n```")
    result = result.replace("{{NEW_CONTEXT}}", new_context_display)
    result = result.replace("{{ALL_CONTEXT}}", all_context_display)
    result = result.replace("{{PRESSURE_LEVEL}}", str(pressure_level))
    
    return result
