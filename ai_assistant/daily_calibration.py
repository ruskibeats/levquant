"""Daily calibration driver for generating NotebookLM-ready prompts.

No external API calls by default. Generates prompts for manual copy-paste into NotebookLM.
"""

from __future__ import annotations

import json
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional


DEFAULT_OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


class DailyAICalibrator:
    """Driver for daily calibration prompting.

    Generates NotebookLM-ready calibration prompts using accumulated context
    and current engine state. No external LLM calls by default.
    """

    # Template version for tracking
    TEMPLATE_VERSION = "LEVQUANT_CALIBRATION_TEMPLATE_v1.0"

    # Lexicon mapping: technical -> plain English
    LEXICON = {
        "UPLS": "Position Strength (0–1)",
        "SV1a": "Right to Bring the Claim (0–1)",
        "SV1b": "Rule-Breaking Leverage (0–1)",
        "SV1c": "Cost Pressure on Them (0–1)",
        "Tripwire": "Pressure Level (0–10)",
        "Tripwire triggered": "Pressure Alert (Yes/No)",
        "Decision": "Recommended Action",
        "Confidence": "Certainty Score",
        "Kill-switches": "Events That Change Everything",
        "Fear index": "Weakest-Link Stress Level (0–1)",
        "Settlement posture": "Stance (NORMAL/URGENT/FORCE)",
        "Floor": "Minimum Offer (GBP)",
        "Base": "Likely Offer (GBP)",
        "Target": "Aim Offer (GBP)",
        "Ceiling": "Maximum Offer (GBP)",
    }

    def __init__(self, llm_client: Optional[Any] = None):
        """Initialize calibrator.

        Args:
            llm_client: Optional interface to an LLM with .query(prompt: str) -> str method.
                       If None (default), build_prompt is used for manual copy-paste.
        """
        self.llm = llm_client

    def build_prompt(
        self,
        all_context: str,
        new_context: str,
        engine_snapshot: dict,
        assumptions_snapshot: dict,
    ) -> str:
        """Build a NotebookLM-ready calibration prompt.

        Args:
            all_context: Concatenated string of all prior journal entries.
            new_context: The new context added today.
            engine_snapshot: Current deterministic engine output.
            assumptions_snapshot: Assumptions dict from monetary corridor module.

        Returns:
            Full prompt string ready for NotebookLM.
        """
        lexicon_block = self._build_lexicon_block()
        snapshot_block = self._build_snapshot_block(engine_snapshot)
        assumptions_block = self._build_assumptions_block(assumptions_snapshot)
        questionnaire_block = self._build_questionnaire_block(engine_snapshot)
        output_schema_block = self._build_output_schema_block()

        prompt = f"""# LEVQUANT DAILY CALIBRATION PROMPT
@{self.TEMPLATE_VERSION}

## 1. ROLE / SYSTEM INSTRUCTION
You are a calibration auditor for the LEVQUANT procedural leverage decision-support system.
Your task is to audit the system's outputs against accumulated evidence and detect drift, fact-status changes, and calibration misalignments.

Rules:
- Use only the evidence provided in the context below.
- Express all claims with bounded probabilities and confidence scores.
- Reference specific evidence IDs (timestamps or entry indices) for every claim.
- Use court-safe language: "alleged", "supported by evidence", "inferred" — never "proven" or absolute claims.
- Output valid JSON only, matching the schema at the end of this prompt.

{lexicon_block}

## 3. CURRENT ENGINE SNAPSHOT (Deterministic Results)
{snapshot_block}

## 4. ASSUMPTIONS SNAPSHOT (Monetary Corridor Module)
{assumptions_block}

## 5. WHAT CHANGED TODAY (New Context)
{new_context if new_context.strip() else "[No new context added today]"}

## 6. FULL CONTEXT (All Previously Accumulated)
{all_context if all_context.strip() else "[No prior context in journal]"}

## 7. CALIBRATION QUESTIONNAIRE
Answer all questions in the output JSON schema below.

{questionnaire_block}

## 8. OUTPUT SCHEMA (JSON ONLY)
{output_schema_block}

---
INSTRUCTION: Output valid JSON only. No markdown, no explanatory text outside the JSON structure.
"""
        return prompt

    def _build_lexicon_block(self) -> str:
        """Build the lexicon section mapping technical to plain English terms."""
        lines = ["## 2. LEXICON (Use These Terms in Output)", ""]
        for tech, plain in self.LEXICON.items():
            lines.append(f"- {tech} -> \"{plain}\"")
        lines.append("")
        lines.append("All output fields should use the plain English terms in parentheses where applicable.")
        return "\n".join(lines)

    def _build_snapshot_block(self, engine_snapshot: dict) -> str:
        """Format the engine snapshot for the prompt."""
        inputs = engine_snapshot.get("inputs", {})
        scores = engine_snapshot.get("scores", {})
        evaluation = engine_snapshot.get("evaluation", {})

        return f"""```json
{{
  "inputs": {json.dumps(inputs, indent=2)},
  "scores": {json.dumps(scores, indent=2)},
  "evaluation": {json.dumps(evaluation, indent=2)}
}}
```

Plain English Summary:
- Position Strength (UPLS): {scores.get('upls', 'N/A')}
- Pressure Level (Tripwire): {scores.get('tripwire', 'N/A')}/10
- Pressure Alert (Tripwire triggered): {'Yes' if evaluation.get('tripwire_triggered') else 'No'}
- Recommended Action (Decision): {evaluation.get('decision', 'N/A')}
- Certainty Score (Confidence): {evaluation.get('confidence', 'N/A')}"""

    def _build_assumptions_block(self, assumptions: dict) -> str:
        """Format assumptions snapshot."""
        return f"""```json
{json.dumps(assumptions, indent=2)}
```

Assumptions Audit Notes:
- Review whether these assumptions are "light" (data-driven) or "heavy" (speculative).
- Flag any assumptions that appear to carry disproportionate weight in the corridor calculation."""

    def _build_questionnaire_block(self, engine_snapshot: dict) -> str:
        """Build the calibration questionnaire."""
        scores = engine_snapshot.get("scores", {})
        tripwire = scores.get("tripwire", 0)

        return f"""### A. Fact Status Validation (CRITICAL: Realised vs Prospective)

**Classification Schema:**
- **REALISED** — Already filed, evidenced, or judicially noticed. Not contingent on future events.
- **EVIDENCED** — Supported by documentary/metadata evidence but may be contested.
- **ALLEGED** — Claimed but not yet evidenced or tested.
- **PROSPECTIVE** — Dependent on future outcomes (hearing, judicial comment, etc.).

For each key fact:
1. **Classification**: REALISED / EVIDENCED / ALLEGED / PROSPECTIVE
2. **Status**: PROVEN / INFERRED / UNKNOWN / CONTESTED
3. **Probability**: (0.0–1.0) — What is the likelihood this fact stands up?
4. **Confidence**: (0.0–1.0) — How certain are you of this classification?
5. **Evidence IDs**: Reference timestamps from context
6. **Error check**: Is this fact misclassified as PROSPECTIVE when it is actually REALISED?

**Common Error to Flag:**
> "Defence validity pending judicial signal" when Defence deadline already expired and no relief sought.

**Correction Rule:**
If a fact is already filed/evidenced → classify as REALISED, not PROSPECTIVE.
This shifts leverage from "anticipatory" to "realised."

### B. Drift Detection
1. Compare today's new context to prior context. What probabilities increased WITHOUT new evidence?
2. Calculate a drift_score (0.0–1.0) where 1.0 = major unexplained shifts.
3. List specific fields where drift is detected.
4. **Specific check**: Are any REALISED facts still being treated as PROSPECTIVE in the assessment?
5. List required corrections to realign the model.

### C. Pressure Level Calibration (Tripwire Check)
Current Pressure Level: {tripwire}/10

1. Is this Pressure Level consistent with the facts and Stance?
2. **Fact Status Impact**: If key facts are REALISED (not PROSPECTIVE), how does that change Pressure Level?
3. If Pressure Level rises by +1 (e.g., new external validation), what changes in:
   - Settlement corridor range?
   - Stance (NORMAL/URGENT/FORCE)?
   - Recommended Action?
4. Explain in plain English why the current Pressure Level is justified or miscalibrated.

### D. Settlement Corridor Sanity Check
Anchor (user objective): £15,000,000
Minimum Acceptable: £9,000,000

1. Does the current corridor (Floor→Ceiling) align with the £9m minimum objective?
2. **Realised Leverage Check**: Are you pricing REALISED facts as if they were PROSPECTIVE?
   - Example: Defence nullity already filed → should price as realised, not pending
3. If Aim/Maximum are far below £9m without justified assumption changes, flag "corridor misalignment".
4. What single new fact would shift the corridor most significantly?
5. Provide reasoning in plain English.

### E. Insurer Behaviour Translation
1. What single new fact causes fastest "reserve rights" behaviour?
2. What triggers "exit or void" from the insurer?
3. What conditions create "settlement urgency spike"?
4. **Realised Risk Timing**: If key facts are already filed, why would insurers wait for April 8 rather than act now?

### F. Breakpoint Stress Analysis
1. Which actor breaks first under pressure? (bounded, evidence-referenced)
2. Why? What is the weakest link in their position?
3. What evidence supports this inference?
4. **Timing Analysis**: What is the cost of delay if key facts are already REALISED?

### G. Daily Actions
1. What should be UPDATED in the model inputs? (specific SV changes, fact reclassifications)
2. What should be LEFT UNCHANGED? (resist overfitting)
3. **Fact Reclassification Priority**: Which PROSPECTIVE facts should be reclassified as REALISED?
4. What should be WATCHED next? (monitoring priorities)"""

    def _build_output_schema_block(self) -> str:
        """Build the output JSON schema description."""
        return """```json
{
  "timestamp_utc": "ISO8601 timestamp of this calibration",
  "model_version": "LEVQUANT_CALIBRATION_TEMPLATE_v1.0",
  "lexicon_used": true,
  "engine_snapshot": {
    "inputs": {"SV1a": 0.0, "SV1b": 0.0, "SV1c": 0.0},
    "scores": {"upls": 0.0, "tripwire": 0.0},
    "evaluation": {"decision": "HOLD|PUSH|FORCE", "confidence": "Low|Moderate|High", "tripwire_triggered": false}
  },
  "assumptions_audit": {
    "assumptions_light_or_heavy": "light|mixed|heavy",
    "top_5_load_bearing_assumptions": ["assumption_key_1", "..."],
    "tripwire_dependency_check": {"pressure_level_sensitivity": "high|medium|low", "notes": "..."}
  },
  "fact_checks": [
    {
      "id": "F1",
      "claim": "description of fact",
      "status": "PROVEN|INFERRED|UNKNOWN",
      "probability": 0.0,
      "confidence": 0.0,
      "evidence_ids": ["timestamp_or_index"],
      "notes": "court-safe caveats"
    }
  ],
  "drift_detection": {
    "drift_score": 0.0,
    "where_drift_detected": ["field_name"],
    "required_corrections": ["action"]
  },
  "tripwire_calibration": {
    "pressure_level_expected": 0,
    "pressure_level_actual": 0,
    "explain_in_plain_english": "..."
  },
  "settlement_corridor_check": {
    "anchor_gbp": 15000000,
    "minimum_objective_gbp": 9000000,
    "corridor_alignment": "aligned|misaligned",
    "why": "...",
    "what_single_new_fact_shifts_corridor_most": "..."
  },
  "insurer_logic": {
    "fastest_scare_fact": "...",
    "reserve_rights_triggers": ["..."],
    "exit_or_void_triggers": ["..."],
    "settlement_urgency_spike_conditions": ["..."]
  },
  "daily_actions": {
    "what_to_update_in_inputs": ["..."],
    "what_to_leave_unchanged": ["..."],
    "what_to_watch_next": ["..."]
  }
}
```"""

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

        result = {
            "date": datetime.now(UTC).isoformat(),
            "new_context": new_context,
            "raw_prompt": prompt,
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
