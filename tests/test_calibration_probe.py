"""Tests for ai_assistant.calibration_probe module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_assistant.calibration_probe import (
    CALIBRATION_PROBE_PROMPT,
    REQUIRED_KEYS,
    compare_probes,
    get_probe_history,
    run_calibration_probe,
)


class TestCalibrationProbePrompt:
    """Tests for the calibration probe prompt template."""

    def test_prompt_contains_machine_only_instruction(self) -> None:
        """Prompt must contain machine-only instruction."""
        assert "Machine-only" in CALIBRATION_PROBE_PROMPT or "machine-only" in CALIBRATION_PROBE_PROMPT.lower()

    def test_prompt_contains_no_advocacy_instruction(self) -> None:
        """Prompt must instruct not to advocate or persuade."""
        assert "not advocate" in CALIBRATION_PROBE_PROMPT.lower()
        assert "persuade" in CALIBRATION_PROBE_PROMPT.lower()  # Part of "not advocate, persuade, or optimise"

    def test_prompt_contains_json_only_requirement(self) -> None:
        """Prompt must require JSON-only output."""
        assert "JSON ONLY" in CALIBRATION_PROBE_PROMPT or "json only" in CALIBRATION_PROBE_PROMPT.lower()

    def test_prompt_contains_all_sections(self) -> None:
        """Prompt must contain all required sections."""
        assert "Section 1: Fact Certainty Assessment" in CALIBRATION_PROBE_PROMPT
        assert "Section 2: Procedural Risk Assessment" in CALIBRATION_PROBE_PROMPT
        assert "Section 3: Counterparty Stress Analysis" in CALIBRATION_PROBE_PROMPT
        assert "Section 4: Settlement Range Sanity Check" in CALIBRATION_PROBE_PROMPT
        assert "Section 5: Drift Detection" in CALIBRATION_PROBE_PROMPT

    def test_prompt_contains_required_output_keys(self) -> None:
        """Prompt must document all required output keys."""
        for key in REQUIRED_KEYS:
            assert key in CALIBRATION_PROBE_PROMPT, f"Required key '{key}' not in prompt"


class TestRunCalibrationProbe:
    """Tests for run_calibration_probe function."""

    def test_prompt_only_mode_no_llm_client(self) -> None:
        """Test that prompt-only mode works without LLM client."""
        engine_snapshot = {
            "inputs": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
            "scores": {"upls": 0.55, "tripwire": 6.5},
            "evaluation": {"decision": "HOLD", "confidence": "Moderate"},
        }
        assumptions_snapshot = {"test_assumption": 0.5}
        
        result = run_calibration_probe(
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=None,
        )
        
        assert result["status"] == "prompt_only"
        assert result["probe_version"] == "1.0"
        assert "timestamp_utc" in result
        assert "prompt" in result
        assert result["parsed_output"] is None
        assert result["error"] is None

    def test_prompt_contains_engine_snapshot(self) -> None:
        """Generated prompt must contain engine snapshot data."""
        engine_snapshot = {
            "inputs": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
            "scores": {"upls": 0.55, "tripwire": 6.5},
            "evaluation": {"decision": "HOLD", "confidence": "Moderate"},
        }
        assumptions_snapshot = {"test_assumption": 0.5}
        
        result = run_calibration_probe(
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=None,
        )
        
        prompt = result["prompt"]
        assert "0.55" in prompt  # UPLS value
        assert "6.5" in prompt   # Tripwire value
        assert "HOLD" in prompt  # Decision

    def test_prompt_contains_assumptions(self) -> None:
        """Generated prompt must contain assumptions."""
        engine_snapshot = {"inputs": {}, "scores": {}, "evaluation": {}}
        assumptions_snapshot = {"test_key": "test_value"}
        
        result = run_calibration_probe(
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=None,
        )
        
        assert "test_key" in result["prompt"]
        assert "test_value" in result["prompt"]

    def test_output_persisted_to_disk(self, tmp_path: Path) -> None:
        """Test that output is saved to disk."""
        engine_snapshot = {"inputs": {}, "scores": {}, "evaluation": {}}
        assumptions_snapshot = {}
        output_dir = tmp_path / "calibration"
        
        result = run_calibration_probe(
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=None,
            output_dir=output_dir,
        )
        
        # Check file was created
        files = list(output_dir.glob("calibration_*.json"))
        assert len(files) == 1
        
        # Check content
        saved = json.loads(files[0].read_text())
        assert saved["status"] == "prompt_only"

    def test_run_with_mock_llm_success(self) -> None:
        """Test successful run with mock LLM client."""
        mock_llm = MagicMock()
        mock_llm.query.return_value = json.dumps({
            "probe_version": "1.0",
            "timestamp_utc": "2024-01-01T00:00:00Z",
            "fact_certainty_index": 0.75,
            "procedural_risk_index": 0.3,
            "insurer_exit_probability": 0.4,
            "law_firm_breakpoint_score": 65,
            "recommended_settlement_range_gbp": "£3m–£5m",
            "drift_alert": False,
        })
        
        engine_snapshot = {"inputs": {}, "scores": {}, "evaluation": {}}
        assumptions_snapshot = {}
        
        result = run_calibration_probe(
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=mock_llm,
        )
        
        assert result["status"] == "completed"
        assert result["parsed_output"] is not None
        assert result["parsed_output"]["fact_certainty_index"] == 0.75
        mock_llm.query.assert_called_once()

    def test_run_with_mock_llm_invalid_json(self) -> None:
        """Test handling of invalid JSON from LLM."""
        mock_llm = MagicMock()
        mock_llm.query.return_value = "not valid json"
        
        engine_snapshot = {"inputs": {}, "scores": {}, "evaluation": {}}
        assumptions_snapshot = {}
        
        with pytest.raises(RuntimeError, match="Calibration probe failed"):
            run_calibration_probe(
                engine_snapshot=engine_snapshot,
                assumptions_snapshot=assumptions_snapshot,
                llm_client=mock_llm,
            )

    def test_run_with_mock_llm_missing_keys(self) -> None:
        """Test handling of missing required keys from LLM."""
        mock_llm = MagicMock()
        mock_llm.query.return_value = json.dumps({
            "probe_version": "1.0",
            "timestamp_utc": "2024-01-01T00:00:00Z",
            # Missing required keys
        })
        
        engine_snapshot = {"inputs": {}, "scores": {}, "evaluation": {}}
        assumptions_snapshot = {}
        
        with pytest.raises(RuntimeError, match="Calibration probe failed"):
            run_calibration_probe(
                engine_snapshot=engine_snapshot,
                assumptions_snapshot=assumptions_snapshot,
                llm_client=mock_llm,
            )

    def test_run_with_markdown_in_output(self) -> None:
        """Test that markdown code blocks are stripped from LLM output."""
        mock_llm = MagicMock()
        mock_llm.query.return_value = """```json
{
  "probe_version": "1.0",
  "timestamp_utc": "2024-01-01T00:00:00Z",
  "fact_certainty_index": 0.75,
  "procedural_risk_index": 0.3,
  "insurer_exit_probability": 0.4,
  "law_firm_breakpoint_score": 65,
  "recommended_settlement_range_gbp": "£3m–£5m",
  "drift_alert": false
}
```"""
        
        engine_snapshot = {"inputs": {}, "scores": {}, "evaluation": {}}
        assumptions_snapshot = {}
        
        result = run_calibration_probe(
            engine_snapshot=engine_snapshot,
            assumptions_snapshot=assumptions_snapshot,
            llm_client=mock_llm,
        )
        
        assert result["status"] == "completed"
        assert result["parsed_output"]["fact_certainty_index"] == 0.75


class TestGetProbeHistory:
    """Tests for get_probe_history function."""

    def test_empty_history(self, tmp_path: Path, monkeypatch) -> None:
        """Test that empty history returns empty list."""
        from ai_assistant import calibration_probe
        monkeypatch.setattr(calibration_probe, "LOG_FILE", tmp_path / "calibration.log")
        
        history = get_probe_history()
        assert history == []

    def test_read_history(self, tmp_path: Path, monkeypatch) -> None:
        """Test reading history from log file."""
        from ai_assistant import calibration_probe
        log_file = tmp_path / "calibration.log"
        monkeypatch.setattr(calibration_probe, "LOG_FILE", log_file)
        
        # Write test entries
        with open(log_file, "w") as f:
            f.write(json.dumps({"timestamp_utc": "2024-01-01", "status": "completed"}) + "\n")
            f.write(json.dumps({"timestamp_utc": "2024-01-02", "status": "completed"}) + "\n")
        
        history = get_probe_history()
        assert len(history) == 2
        assert history[0]["timestamp_utc"] == "2024-01-01"

    def test_history_limit(self, tmp_path: Path, monkeypatch) -> None:
        """Test that limit parameter works."""
        from ai_assistant import calibration_probe
        log_file = tmp_path / "calibration.log"
        monkeypatch.setattr(calibration_probe, "LOG_FILE", log_file)
        
        # Write test entries
        with open(log_file, "w") as f:
            for i in range(5):
                f.write(json.dumps({"timestamp_utc": f"2024-01-0{i+1}", "status": "completed"}) + "\n")
        
        history = get_probe_history(limit=3)
        assert len(history) == 3
        # Should get last 3 entries
        assert history[0]["timestamp_utc"] == "2024-01-03"


class TestCompareProbes:
    """Tests for compare_probes function."""

    def test_compare_returns_placeholder(self) -> None:
        """Test that compare_probes returns placeholder for now."""
        result = compare_probes("2024-01-01", "2024-01-02")
        assert result["comparison_status"] == "not_implemented"
        assert result["timestamp_a"] == "2024-01-01"
        assert result["timestamp_b"] == "2024-01-02"


class TestValidation:
    """Tests for output validation."""

    def test_validate_numeric_ranges(self) -> None:
        """Test that numeric values are validated."""
        from ai_assistant.calibration_probe import _validate_probe_output
        
        # Valid output
        valid = {
            "probe_version": "1.0",
            "timestamp_utc": "2024-01-01",
            "fact_certainty_index": 0.75,
            "procedural_risk_index": 0.3,
            "insurer_exit_probability": 0.4,
            "law_firm_breakpoint_score": 65,
            "recommended_settlement_range_gbp": "£3m–£5m",
            "drift_alert": False,
        }
        _validate_probe_output(valid)  # Should not raise

    def test_validate_probability_out_of_range(self) -> None:
        """Test that probabilities outside 0-1 are rejected."""
        from ai_assistant.calibration_probe import _validate_probe_output
        
        invalid = {
            "probe_version": "1.0",
            "timestamp_utc": "2024-01-01",
            "fact_certainty_index": 1.5,  # Invalid: > 1
            "procedural_risk_index": 0.3,
            "insurer_exit_probability": 0.4,
            "law_firm_breakpoint_score": 65,
            "recommended_settlement_range_gbp": "£3m–£5m",
            "drift_alert": False,
        }
        
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            _validate_probe_output(invalid)

    def test_validate_breakpoint_score_range(self) -> None:
        """Test that breakpoint score outside 0-100 is rejected."""
        from ai_assistant.calibration_probe import _validate_probe_output
        
        invalid = {
            "probe_version": "1.0",
            "timestamp_utc": "2024-01-01",
            "fact_certainty_index": 0.75,
            "procedural_risk_index": 0.3,
            "insurer_exit_probability": 0.4,
            "law_firm_breakpoint_score": 150,  # Invalid: > 100
            "recommended_settlement_range_gbp": "£3m–£5m",
            "drift_alert": False,
        }
        
        with pytest.raises(ValueError, match="must be integer 0–100"):
            _validate_probe_output(invalid)

    def test_validate_drift_alert_type(self) -> None:
        """Test that drift_alert must be boolean."""
        from ai_assistant.calibration_probe import _validate_probe_output
        
        invalid = {
            "probe_version": "1.0",
            "timestamp_utc": "2024-01-01",
            "fact_certainty_index": 0.75,
            "procedural_risk_index": 0.3,
            "insurer_exit_probability": 0.4,
            "law_firm_breakpoint_score": 65,
            "recommended_settlement_range_gbp": "£3m–£5m",
            "drift_alert": "false",  # Invalid: string instead of bool
        }
        
        with pytest.raises(ValueError, match="drift_alert must be boolean"):
            _validate_probe_output(invalid)
