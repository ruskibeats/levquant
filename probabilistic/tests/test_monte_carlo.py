"""
Tests for Monte Carlo sampling.

This test module verifies Monte Carlo distribution sampling
and aggregation without importing from /engine directly.

Critical Design Principle:
    All tests must use probabilistic.adapters.run_deterministic_engine().
    Never import from /engine directly.
"""

import pytest
import numpy as np
from probabilistic.monte_carlo import (
    UniformDistribution,
    NormalDistribution,
    BetaDistribution,
    TriangularDistribution,
    monte_carlo_sample
)
from probabilistic.adapters import run_deterministic_engine, batch_run


class TestUniformDistribution:
    """Test UniformDistribution sampling."""
    
    def test_uniform_samples_in_range(self):
        """Test that samples are within specified range."""
        dist = UniformDistribution(0.2, 0.8)
        samples = dist.sample(1000)
        
        assert samples.min() >= 0.2
        assert samples.max() <= 0.8
        assert len(samples) == 1000
        
    def test_uniform_mean_centered(self):
        """Test that uniform distribution mean is centered."""
        dist = UniformDistribution(0.0, 1.0)
        samples = dist.sample(10000)
        
        assert abs(samples.mean() - 0.5) < 0.05  # Should be near 0.5


class TestNormalDistribution:
    """Test NormalDistribution sampling."""
    
    def test_normal_samples_clipped(self):
        """Test that normal samples are clipped to [0, 1]."""
        dist = NormalDistribution(mean=0.5, std=0.1)
        samples = dist.sample(1000)
        
        assert samples.min() >= 0.0
        assert samples.max() <= 1.0
        assert len(samples) == 1000
        
    def test_normal_mean_approx_target(self):
        """Test that normal mean approximates target."""
        dist = NormalDistribution(mean=0.6, std=0.05)
        samples = dist.sample(10000)
        
        assert abs(samples.mean() - 0.6) < 0.05


class TestBetaDistribution:
    """Test BetaDistribution sampling."""
    
    def test_beta_samples_in_range(self):
        """Test that beta samples are in [0, 1]."""
        dist = BetaDistribution(alpha=2.0, beta=5.0)
        samples = dist.sample(1000)
        
        assert samples.min() >= 0.0
        assert samples.max() <= 1.0
        assert len(samples) == 1000


class TestTriangularDistribution:
    """Test TriangularDistribution sampling."""
    
    def test_triangular_samples_in_range(self):
        """Test that triangular samples are in range."""
        dist = TriangularDistribution(min_val=0.2, mode=0.5, max_val=0.8)
        samples = dist.sample(1000)
        
        assert samples.min() >= 0.2
        assert samples.max() <= 0.8
        assert len(samples) == 1000


class TestBatchRun:
    """Test batch execution for Monte Carlo."""
    
    def test_batch_run_returns_correct_count(self):
        """Test that batch_run returns correct number of results."""
        states = [
            {'SV1a': 0.5, 'SV1b': 0.5, 'SV1c': 0.5},
            {'SV1a': 0.3, 'SV1b': 0.7, 'SV1c': 0.9},
            {'SV1a': 0.8, 'SV1b': 0.8, 'SV1c': 0.8}
        ]
        
        results = batch_run(states)
        
        assert len(results) == 3
        
    def test_batch_run_validates_states(self):
        """Test that batch_run validates SV values."""
        # Valid states should work
        valid_states = [
            {'SV1a': 0.38, 'SV1b': 0.86, 'SV1c': 0.75}
        ]
        
        results = batch_run(valid_states)
        assert len(results) == 1
        assert results[0].evaluation.decision in ['ACCEPT', 'COUNTER', 'REJECT', 'HOLD']


class TestMonteCarloSampling:
    """Test Monte Carlo sampling function (skeleton tests)."""
    
    def test_monte_carlo_returns_structure(self):
        """Test that monte_carlo_sample returns correct structure."""
        # Small sample size for speed
        sv1a_dist = UniformDistribution(0.3, 0.4)
        sv1b_dist = UniformDistribution(0.8, 0.9)
        sv1c_dist = UniformDistribution(0.7, 0.8)
        
        result = monte_carlo_sample(
            n_samples=10,
            sv1a_dist=sv1a_dist,
            sv1b_dist=sv1b_dist,
            sv1c_dist=sv1c_dist
        )
        
        # Check structure
        assert 'meta' in result
        assert 'distributions' in result
        assert 'decision_frequencies' in result
        assert 'decision_proportions' in result
        assert result.meta['n_samples'] == 10
        
        # Check that all decisions are present
        for decision in ['ACCEPT', 'COUNTER', 'REJECT', 'HOLD']:
            assert decision in result.decision_frequencies
            assert decision in result.decision_proportions
            
    def test_monte_carlo_proportions_sum_to_one(self):
        """Test that decision proportions sum to 1.0."""
        sv1a_dist = UniformDistribution(0.3, 0.4)
        sv1b_dist = UniformDistribution(0.8, 0.9)
        sv1c_dist = UniformDistribution(0.7, 0.8)
        
        result = monte_carlo_sample(
            n_samples=100,
            sv1a_dist=sv1a_dist,
            sv1b_dist=sv1b_dist,
            sv1c_dist=sv1c_dist
        )
        
        total = sum(result.decision_proportions.values())
        assert abs(total - 1.0) < 0.01  # Floating point tolerance
        
    def test_monte_carlo_distributions_present(self):
        """Test that distribution parameters are calculated."""
        sv1a_dist = UniformDistribution(0.3, 0.4)
        sv1b_dist = UniformDistribution(0.8, 0.9)
        sv1c_dist = UniformDistribution(0.7, 0.8)
        
        result = monte_carlo_sample(
            n_samples=10,
            sv1a_dist=sv1a_dist,
            sv1b_dist=sv1b_dist,
            sv1c_dist=sv1c_dist
        )
        
        # Check SV distribution parameters
        assert 'sv1a' in result.distributions
        assert 'sv1b' in result.distributions
        assert 'sv1c' in result.distributions
        
        # Check that each has mean and std
        for sv in ['sv1a', 'sv1b', 'sv1c']:
            assert 'mean' in result.distributions[sv]
            assert 'std' in result.distributions[sv]