"""
Tests for predefined scenarios.

This test module verifies that all predefined scenarios run successfully
and return valid outputs. It does not import from /engine directly.

Critical Design Principle:
    All tests must use probabilistic.adapters.run_deterministic_engine().
    Never import from /engine directly.
"""

import pytest
from probabilistic.scenarios import (
    run_scenario,
    run_all_scenarios,
    run_custom_scenario,
    list_scenarios,
    get_scenario_description,
    SCENARIOS
)
from probabilistic.schemas import ScenarioResult


class TestScenarioExecution:
    """Test scenario execution for individual named scenarios."""
    
    def test_run_cost_spike_scenario(self):
        """Test cost_spike scenario runs successfully."""
        result = run_scenario('cost_spike')
        
        # Check that result is valid
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'cost_spike'
        assert result.description != ''
        
        # Check that deterministic engine ran
        assert result.output.evaluation.decision in ['ACCEPT', 'COUNTER', 'REJECT', 'HOLD']
        assert result.output.version == "1.0"
        
    def test_run_invalidity_collapse_scenario(self):
        """Test invalidity_collapse scenario runs successfully."""
        result = run_scenario('invalidity_collapse')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'invalidity_collapse'
        assert result.output.evaluation.decision == 'REJECT'  # SV1a minimized
        
    def test_run_procedural_loss_scenario(self):
        """Test procedural_loss scenario runs successfully."""
        result = run_scenario('procedural_loss')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'procedural_loss'
        assert result.output.evaluation.decision == 'REJECT'  # SV1b minimized
        
    def test_run_judge_hostile_scenario(self):
        """Test judge_hostile scenario runs successfully."""
        result = run_scenario('judge_hostile')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'judge_hostile'
        assert result.output.evaluation.decision in ['REJECT', 'COUNTER', 'HOLD', 'ACCEPT']  # Could be any
        
    def test_run_perfect_case_scenario(self):
        """Test perfect_case scenario runs successfully."""
        result = run_scenario('perfect_case')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'perfect_case'
        assert result.output.evaluation.decision == 'ACCEPT'  # All SVs maximized
        
    def test_run_worst_case_scenario(self):
        """Test worst_case scenario runs successfully."""
        result = run_scenario('worst_case')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'worst_case'
        assert result.output.evaluation.decision == 'REJECT'  # All SVs minimized
        
    def test_run_cost_neutral_scenario(self):
        """Test cost_neutral scenario runs successfully."""
        result = run_scenario('cost_neutral')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'cost_neutral'
        assert result.output.scores.sv1c == 0.5  # SV1c at 0.5
        
    def test_run_claim_moderate_scenario(self):
        """Test claim_moderate scenario runs successfully."""
        result = run_scenario('claim_moderate')
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'claim_moderate'
        assert result.output.inputs.sv1a == 0.5  # SV1a at 0.5


class TestCustomScenarios:
    """Test custom scenario execution and validation."""
    
    def test_run_custom_mixed_scenario(self):
        """Test custom scenario with mixed SV values."""
        result = run_custom_scenario(
            scenario_name='mixed_case',
            sv1a=0.6,
            sv1b=0.4,
            sv1c=0.8,
            description='Mixed signals across all factors'
        )
        
        assert isinstance(result, ScenarioResult)
        assert result.scenario_name == 'mixed_case'
        assert result.output.inputs.sv1a == 0.6
        assert result.output.inputs.sv1b == 0.4
        assert result.output.inputs.sv1c == 0.8
        
    def test_custom_scenario_bounds_validation(self):
        """Test that custom scenarios validate SV bounds [0.0, 1.0]."""
        # Test SV1a lower bound
        with pytest.raises(ValueError) as exc_info:
            run_custom_scenario(
                scenario_name='sv1a_below_zero',
                sv1a=-0.1,
                sv1b=0.5,
                sv1c=0.5,
                description='Invalid SV1a'
            )
        assert 'SV1a' in str(exc_info.value)
        assert '0.0, 1.0' in str(exc_info.value)
        
        # Test SV1a upper bound
        with pytest.raises(ValueError) as exc_info:
            run_custom_scenario(
                scenario_name='sv1a_above_one',
                sv1a=1.1,
                sv1b=0.5,
                sv1c=0.5,
                description='Invalid SV1a'
            )
        assert 'SV1a' in str(exc_info.value)
        assert '0.0, 1.0' in str(exc_info.value)


class TestScenarioListing:
    """Test scenario listing and description functions."""
    
    def test_list_scenarios_returns_all_names(self):
        """Test that list_scenarios returns all predefined scenario names."""
        names = list_scenarios()
        
        assert isinstance(names, list)
        assert len(names) == 8  # 8 predefined scenarios
        assert 'cost_spike' in names
        assert 'invalidity_collapse' in names
        assert 'procedural_loss' in names
        assert 'perfect_case' in names
        assert 'worst_case' in names
        assert 'judge_hostile' in names
        assert 'cost_neutral' in names
        assert 'claim_moderate' in names
        
    def test_list_scenarios_names_are_strings(self):
        """Test that all scenario names are strings."""
        names = list_scenarios()
        
        for name in names:
            assert isinstance(name, str)
            
    def test_get_scenario_description_returns_correct_description(self):
        """Test that get_scenario_description returns correct descriptions."""
        desc = get_scenario_description('cost_spike')
        assert 'Maximum cost asymmetry' in desc
        
        desc = get_scenario_description('invalidity_collapse')
        assert 'Minimum claim validity' in desc
        
        desc = get_scenario_description('worst_case')
        assert 'All factors minimized' in desc
        
    def test_get_scenario_description_raises_for_unknown_scenario(self):
        """Test that get_scenario_description raises ValueError for unknown scenario."""
        with pytest.raises(ValueError) as exc_info:
            get_scenario_description('unknown_scenario')
        
        assert 'Unknown scenario' in str(exc_info.value)
        assert 'unknown_scenario' in str(exc_info.value)


class TestBatchScenarioExecution:
    """Test running all scenarios at once."""
    
    def test_run_all_scenarios_returns_correct_count(self):
        """Test that run_all_scenarios returns correct number of results."""
        results = run_all_scenarios()
        
        assert isinstance(results, list)
        assert len(results) == 8  # 8 predefined scenarios
        
        # Verify each result is valid
        for result in results:
            assert isinstance(result, ScenarioResult)
            assert result.scenario_name != ''
            assert result.output.evaluation.decision in ['ACCEPT', 'COUNTER', 'REJECT', 'HOLD']
            
    def test_run_all_scenarios_all_have_valid_decisions(self):
        """Test that all scenarios produce valid decisions."""
        results = run_all_scenarios()
        
        # Expected decisions for each scenario
        expected_decisions = {
            'cost_spike': 'HOLD',  # High SV1c triggers HOLD
            'invalidity_collapse': 'REJECT',  # Low SV1a triggers REJECT
            'procedural_loss': 'REJECT',  # Low SV1b triggers REJECT
            'perfect_case': 'ACCEPT',  # High SVs trigger ACCEPT
            'worst_case': 'REJECT',  # Low SVs trigger REJECT
            'judge_hostile': 'ACCEPT',  # High SV1a, low SV1b still gives ACCEPT
            'cost_neutral': 'HOLD',  # Mixed signals give HOLD
            'claim_moderate': 'HOLD'  # Lower SV1a gives HOLD
        }
        
        for result in results:
            assert result.evaluation.decision == expected_decisions[result.scenario_name]