"""
CLI output tests.

This test verifies that the CLI produces correct output in both
human-readable and JSON modes.
"""

import sys
import json
from io import StringIO
import pytest
from cli.run import main, run_engine


class TestRunEngine:
    """
    Test the run_engine() helper function.
    """
    
    def test_run_engine_structure(self):
        """Test that run_engine returns expected structure."""
        result = run_engine()
        
        # Check all required keys are present
        assert 'inputs' in result
        assert 'scores' in result
        assert 'evaluation' in result
        assert 'interpretation' in result
        assert 'version' in result
        
    def test_run_engine_types(self):
        """Test that run_engine returns correct types."""
        result = run_engine()
        
        assert isinstance(result['inputs'], dict)
        assert isinstance(result['scores'], dict)
        assert isinstance(result['evaluation'], dict)
        assert isinstance(result['interpretation'], dict)
        assert isinstance(result['version'], str)
        
    def test_run_engine_values(self):
        """Test that run_engine computes correct values."""
        result = run_engine()
        
        # Check inputs
        assert 'SV1a' in result['inputs']
        assert 'SV1b' in result['inputs']
        assert 'SV1c' in result['inputs']
        
        # Check scores
        assert 'upls' in result['scores']
        assert 'tripwire' in result['scores']
        assert result['scores']['upls'] == 0.641
        assert result['scores']['tripwire'] == 6.41
        
        # Check evaluation
        assert 'decision' in result['evaluation']
        assert 'confidence' in result['evaluation']
        assert 'tripwire_triggered' in result['evaluation']
        
        # Check interpretation
        assert 'leverage_position' in result['interpretation']
        assert 'decision_explanation' in result['interpretation']
        assert 'tripwire_status' in result['interpretation']
        assert 'confidence_explanation' in result['interpretation']
        
        # Check version
        assert result['version'] == "1.0"
        
    def test_run_engine_custom_state(self):
        """Test that run_engine accepts custom state."""
        custom_state = {'SV1a': 0.90, 'SV1b': 0.95, 'SV1c': 0.80}
        result = run_engine(state=custom_state)
        
        assert result['inputs'] == custom_state
        assert result['scores']['upls'] == 0.893  # (0.40*0.90 + 0.35*0.95 + 0.25*0.80)
        assert result['evaluation']['decision'] == "ACCEPT"


class TestCLIOutput:
    """
    Test CLI output in different modes.
    """
    
    def test_human_mode_output(self, capsys):
        """Test CLI in human-readable mode (default)."""
        exit_code = main([])
        
        # Check exit code
        assert exit_code == 0
        
        # Check stdout
        captured = capsys.readouterr()
        output = captured.out
        
        # Check for expected sections
        assert "PROCEDURAL LEVERAGE ENGINE - CASE ANALYSIS" in output
        assert "INPUTS:" in output
        assert "SCORES:" in output
        assert "DECISION:" in output
        assert "INTERPRETATION:" in output
        
        # Check for expected values
        assert "0.38" in output  # SV1a
        assert "0.86" in output  # SV1b
        assert "0.75" in output  # SV1c
        assert "0.641" in output  # UPLS
        assert "6.41" in output  # Tripwire
        assert "HOLD" in output  # Decision
        assert "Moderate" in output  # Confidence
        
        # Check that stderr is empty
        assert captured.err == ""
        
    def test_json_mode_output(self, capsys):
        """Test CLI in JSON mode."""
        exit_code = main(['--json'])
        
        # Check exit code
        assert exit_code == 0
        
        # Check stdout
        captured = capsys.readouterr()
        output = captured.out
        
        # Parse JSON
        result = json.loads(output)
        
        # Verify schema
        assert 'inputs' in result
        assert 'scores' in result
        assert 'evaluation' in result
        assert 'interpretation' in result
        assert 'version' in result
        
        # Verify values
        assert result['inputs']['SV1a'] == 0.38
        assert result['scores']['upls'] == 0.641
        assert result['evaluation']['decision'] == "HOLD"
        assert result['version'] == "1.0"
        
        # Check that stderr is empty
        assert captured.err == ""
        
    def test_json_short_flag(self, capsys):
        """Test CLI with -j short flag."""
        exit_code = main(['-j'])
        
        assert exit_code == 0
        captured = capsys.readouterr()
        
        # Should be valid JSON
        result = json.loads(captured.out)
        assert 'inputs' in result
        
    def test_json_schema_completeness(self, capsys):
        """Test that JSON output includes all required fields."""
        exit_code = main(['--json'])
        
        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        
        # Verify complete schema
        assert set(result['inputs'].keys()) == {'SV1a', 'SV1b', 'SV1c'}
        assert set(result['scores'].keys()) == {'upls', 'tripwire'}
        assert set(result['evaluation'].keys()) == {'decision', 'confidence', 'tripwire_triggered', 'upls_value', 'tripwire_value'}
        assert set(result['interpretation'].keys()) == {'leverage_position', 'decision_explanation', 'tripwire_status', 'confidence_explanation'}
        assert 'version' in result
        
    def test_help_text(self, capsys):
        """Test CLI help text."""
        with pytest.raises(SystemExit) as exc_info:
            main(['--help'])
        
        # argparse exits with 0 for --help
        assert exc_info.value.code == 0
        
        captured = capsys.readouterr()
        
        # Check for help content
        assert "Procedural Leverage Engine" in captured.out
        assert "--json" in captured.out
        assert "-j" in captured.out
        assert "JSON" in captured.out


class TestCLIErrors:
    """
    Test CLI error handling.
    """
    
    def test_invalid_flag(self, capsys):
        """Test CLI with invalid flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(['--invalid'])
        
        # argparse exits with 2 for invalid arguments
        assert exc_info.value.code == 2
        
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()
        assert "unrecognized arguments" in captured.err.lower()
        
    def test_missing_state_key(self, capsys):
        """Test CLI with invalid state (missing key)."""
        # This is harder to test without mocking get_current_state
        # For now, we skip this test
        pass