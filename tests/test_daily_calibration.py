"""Tests for ai_assistant.daily_calibration module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai_assistant.daily_calibration import (
    DailyAICalibrator,
    export_prompt_markdown,
    parse_llm_output,
    save_daily_report,
)


class TestDailyAICalibrator:
    """Tests for DailyAICalibrator class."""

    def test_build_prompt_contains_template_tag(self) -> None:
        """Test that build_prompt includes the template version tag."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="Previous context",
            new_context="New context today",
            engine_snapshot={
                "inputs": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
                "scores": {"upls": 0.55, "tripwire": 6.5},
                "evaluation": {"decision": "HOLD", "confidence": "Moderate", "tripwire_triggered": False},
            },
            assumptions_snapshot={"test_assumption": 0.5},
        )

        assert "@LEVQUANT_CALIBRATION_TEMPLATE_v1.0" in prompt
        assert "Calibration Auditor" in prompt or "calibration auditor" in prompt.lower()

    def test_build_prompt_contains_lexicon(self) -> None:
        """Test that build_prompt includes the lexicon section."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
                "scores": {"upls": 0.55, "tripwire": 6.5},
                "evaluation": {"decision": "HOLD", "confidence": "Moderate", "tripwire_triggered": False},
            },
            assumptions_snapshot={},
        )

        # Check for plain English lexicon mappings
        assert "Position Strength" in prompt or "UPLS" in prompt
        assert "Pressure Level" in prompt or "Tripwire" in prompt
        assert "Right to Bring the Claim" in prompt or "SV1a" in prompt

    def test_build_prompt_contains_engine_snapshot(self) -> None:
        """Test that build_prompt includes engine snapshot data."""
        calibrator = DailyAICalibrator()
        engine_snapshot = {
            "inputs": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
            "scores": {"upls": 0.55, "tripwire": 6.5},
            "evaluation": {"decision": "HOLD", "confidence": "Moderate", "tripwire_triggered": False},
        }

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot=engine_snapshot,
            assumptions_snapshot={},
        )

        assert "0.55" in prompt  # UPLS value
        assert "6.5" in prompt   # Tripwire value
        assert "HOLD" in prompt  # Decision

    def test_build_prompt_contains_assumptions(self) -> None:
        """Test that build_prompt includes assumptions snapshot."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={"test_key": "test_value"},
        )

        assert "test_key" in prompt
        assert "test_value" in prompt

    def test_build_prompt_contains_context(self) -> None:
        """Test that build_prompt includes both old and new context."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="Old context here",
            new_context="New context today",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "Old context here" in prompt
        assert "New context today" in prompt

    def test_build_prompt_contains_questionnaire(self) -> None:
        """Test that build_prompt includes the calibration questionnaire."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "Fact Status Validation" in prompt or "Calibration Questionnaire" in prompt
        assert "Drift Detection" in prompt
        assert "Settlement Corridor Sanity Check" in prompt or "corridor" in prompt.lower()

    def test_build_prompt_contains_output_schema(self) -> None:
        """Test that build_prompt includes the JSON output schema."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "timestamp_utc" in prompt
        assert "model_version" in prompt
        assert "JSON ONLY" in prompt or "valid JSON" in prompt.lower()

    def test_run_without_llm_returns_prompt(self) -> None:
        """Test that run() returns prompt when no LLM client provided."""
        calibrator = DailyAICalibrator(llm_client=None)

        result = calibrator.run(
            new_context="New test",
            all_context="Old test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "date" in result
        assert "new_context" in result
        assert "raw_prompt" in result
        assert result["new_context"] == "New test"
        assert result["llm_response_json"] is None
        assert result["delta_summary"] is None
        assert "@LEVQUANT_CALIBRATION_TEMPLATE" in result["raw_prompt"]

    def test_run_with_llm_calls_client(self) -> None:
        """Test that run() calls LLM client when provided."""
        mock_llm = MagicMock()
        mock_llm.query.return_value = json.dumps({"test": "response"})

        calibrator = DailyAICalibrator(llm_client=mock_llm)

        result = calibrator.run(
            new_context="New test",
            all_context="Old test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        mock_llm.query.assert_called_once()
        assert result["llm_response_json"] == {"test": "response"}
        assert result["delta_summary"] is not None

    def test_run_handles_llm_error(self) -> None:
        """Test that run() handles LLM errors gracefully."""
        mock_llm = MagicMock()
        mock_llm.query.side_effect = Exception("LLM connection failed")

        calibrator = DailyAICalibrator(llm_client=mock_llm)

        result = calibrator.run(
            new_context="New test",
            all_context="Old test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "llm_error" in result
        assert "LLM connection failed" in result["llm_error"]


class TestParseLlmOutput:
    """Tests for parse_llm_output function."""

    def test_parses_valid_json(self) -> None:
        """Test parsing valid JSON string."""
        output = '{"key": "value", "number": 42}'

        result = parse_llm_output(output)

        assert result == {"key": "value", "number": 42}

    def test_parses_json_with_markdown_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        output = '```json\n{"key": "value"}\n```'

        result = parse_llm_output(output)

        assert result == {"key": "value"}

    def test_parses_json_with_generic_code_block(self) -> None:
        """Test parsing JSON wrapped in generic markdown code block."""
        output = '```\n{"key": "value"}\n```'

        result = parse_llm_output(output)

        assert result == {"key": "value"}

    def test_raises_on_invalid_json(self) -> None:
        """Test that invalid JSON raises ValueError."""
        output = "not valid json"

        with pytest.raises(ValueError, match="not valid JSON"):
            parse_llm_output(output)

    def test_raises_on_empty_string(self) -> None:
        """Test that empty string raises ValueError."""
        output = ""

        with pytest.raises(ValueError):
            parse_llm_output(output)


class TestSaveDailyReport:
    """Tests for save_daily_report function."""

    def test_saves_report_with_timestamp(self, tmp_path: Path) -> None:
        """Test that report is saved with timestamp in filename."""
        report = {"date": "2024-01-01T12:00:00", "test": "data"}

        result_path = save_daily_report(report, outputs_dir=tmp_path)

        assert result_path.exists()
        assert result_path.name.startswith("daily_ai_")
        assert result_path.name.endswith(".json")
        assert result_path.parent == tmp_path

        # Verify content
        saved_data = json.loads(result_path.read_text())
        assert saved_data["test"] == "data"

    def test_creates_outputs_dir_if_missing(self, tmp_path: Path) -> None:
        """Test that outputs directory is created if it doesn't exist."""
        report = {"test": "data"}
        outputs_dir = tmp_path / "new_outputs_dir"
        assert not outputs_dir.exists()

        save_daily_report(report, outputs_dir=outputs_dir)

        assert outputs_dir.exists()


class TestExportPromptMarkdown:
    """Tests for export_prompt_markdown function."""

    def test_exports_prompt_to_markdown(self, tmp_path: Path) -> None:
        """Test that prompt is exported as markdown file."""
        prompt = "# Test Prompt\n\nThis is a test."

        result_path = export_prompt_markdown(prompt, outputs_dir=tmp_path)

        assert result_path.exists()
        assert result_path.name.startswith("daily_prompt_")
        assert result_path.name.endswith(".md")
        assert result_path.read_text() == prompt

    def test_creates_outputs_dir_if_missing(self, tmp_path: Path) -> None:
        """Test that outputs directory is created if it doesn't exist."""
        prompt = "Test"
        outputs_dir = tmp_path / "markdown_outputs"
        assert not outputs_dir.exists()

        export_prompt_markdown(prompt, outputs_dir=outputs_dir)

        assert outputs_dir.exists()


class TestCalibrationOutputStructure:
    """Tests verifying the expected output structure matches spec."""

    def test_expected_json_schema_in_prompt(self) -> None:
        """Verify the prompt contains the expected output schema fields."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
                "scores": {"upls": 0.55, "tripwire": 6.5},
                "evaluation": {"decision": "HOLD", "confidence": "Moderate", "tripwire_triggered": False},
            },
            assumptions_snapshot={"leverage_multiplier_min": 0.05},
        )

        # Check for required schema fields
        required_fields = [
            "timestamp_utc",
            "model_version",
            "lexicon_used",
            "engine_snapshot",
            "assumptions_audit",
            "fact_checks",
            "drift_detection",
            "tripwire_calibration",
            "settlement_corridor_check",
            "insurer_logic",
            "daily_actions",
        ]

        for field in required_fields:
            assert field in prompt, f"Required field '{field}' not found in prompt schema"

    def test_pressure_level_calibration_in_questionnaire(self) -> None:
        """Verify the questionnaire includes Pressure Level calibration."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 7.5},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "7.5" in prompt  # Tripwire value should appear
        assert "Pressure Level" in prompt or "Tripwire" in prompt

    def test_settlement_corridor_anchors_in_questionnaire(self) -> None:
        """Verify the questionnaire includes £15m anchor and £9m minimum."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        assert "15000000" in prompt or "£15,000,000" in prompt or "£15m" in prompt.lower()
        assert "9000000" in prompt or "£9,000,000" in prompt or "£9m" in prompt.lower()

    def test_court_safe_language_in_instructions(self) -> None:
        """Verify the prompt includes court-safe language instructions."""
        calibrator = DailyAICalibrator()

        prompt = calibrator.build_prompt(
            all_context="",
            new_context="Test",
            engine_snapshot={
                "inputs": {},
                "scores": {"upls": 0.5, "tripwire": 5.0},
                "evaluation": {},
            },
            assumptions_snapshot={},
        )

        # Check for court-safe language guidance
        assert "alleged" in prompt.lower() or "court-safe" in prompt.lower() or "supported by evidence" in prompt.lower()
