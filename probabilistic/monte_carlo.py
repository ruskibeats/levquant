"""
Monte Carlo sampling for probabilistic extensions.

This file provides distribution sampling and aggregation on top of the
deterministic engine. It does not import from /engine.

Critical Design Principle:
    Use probabilistic.adapters.run_deterministic_engine() to get results.
    Never import from /engine directly.

Status: v2.0-skeleton (structure only, not implemented)
"""

from typing import Dict, List
import numpy as np
from probabilistic.adapters import run_deterministic_engine, batch_run
from probabilistic.schemas import MonteCarloResult


class Distribution:
    """
    Base class for probability distributions.
    
    Subclasses provide sampling methods for SV parameters.
    """
    
    def sample(self, n: int) -> np.ndarray:
        """
        Generate n samples from this distribution.
        
        Args:
            n: Number of samples to generate
        
        Returns:
            numpy array of shape (n,)
        """
        raise NotImplementedError("Subclasses must implement sample()")


class UniformDistribution(Distribution):
    """Uniform distribution between min and max."""
    
    def __init__(self, min_val: float, max_val: float):
        """
        Initialize uniform distribution.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
        """
        self.min_val = min_val
        self.max_val = max_val
    
    def sample(self, n: int) -> np.ndarray:
        """Sample from uniform distribution."""
        return np.random.uniform(self.min_val, self.max_val, size=n)


class NormalDistribution(Distribution):
    """Normal (Gaussian) distribution with clipping to [0, 1]."""
    
    def __init__(self, mean: float, std: float):
        """
        Initialize normal distribution.
        
        Args:
            mean: Mean of distribution
            std: Standard deviation of distribution
        """
        self.mean = mean
        self.std = std
    
    def sample(self, n: int) -> np.ndarray:
        """Sample from normal distribution, clipped to [0, 1]."""
        samples = np.random.normal(self.mean, self.std, size=n)
        return np.clip(samples, 0.0, 1.0)


class BetaDistribution(Distribution):
    """Beta distribution (useful for bounded [0, 1] variables)."""
    
    def __init__(self, alpha: float, beta: float):
        """
        Initialize beta distribution.
        
        Args:
            alpha: Shape parameter (concentration near 1.0)
            beta: Shape parameter (concentration near 0.0)
        """
        self.alpha = alpha
        self.beta = beta
    
    def sample(self, n: int) -> np.ndarray:
        """Sample from beta distribution."""
        return np.random.beta(self.alpha, self.beta, size=n)


class TriangularDistribution(Distribution):
    """Triangular distribution with min, mode, max."""
    
    def __init__(self, min_val: float, mode: float, max_val: float):
        """
        Initialize triangular distribution.
        
        Args:
            min_val: Minimum value
            mode: Mode (most likely value)
            max_val: Maximum value
        """
        self.min_val = min_val
        self.mode = mode
        self.max_val = max_val
    
    def sample(self, n: int) -> np.ndarray:
        """Sample from triangular distribution."""
        return np.random.triangular(
            self.min_val,
            self.mode,
            self.max_val,
            size=n
        )


def monte_carlo_sample(
    n_samples: int,
    sv1a_dist: Distribution,
    sv1b_dist: Distribution,
    sv1c_dist: Distribution
) -> MonteCarloResult:
    """
    Perform Monte Carlo sampling over SV parameters.
    
    Samples from distributions for SV1a, SV1b, SV1c, runs deterministic
    engine for each sample, and aggregates results.
    
    Args:
        n_samples: Number of Monte Carlo samples
        sv1a_dist: Distribution for SV1a
        sv1b_dist: Distribution for SV1b
        sv1c_dist: Distribution for SV1c
    
    Returns:
        MonteCarloResult with aggregated statistics
    
    Example:
        >>> sv1a_dist = NormalDistribution(mean=0.38, std=0.05)
        >>> sv1b_dist = NormalDistribution(mean=0.86, std=0.03)
        >>> sv1c_dist = NormalDistribution(mean=0.75, std=0.08)
        >>> result = monte_carlo_sample(10000, sv1a_dist, sv1b_dist, sv1c_dist)
        >>> print(result.decision_proportions)
    """
    # Sample from distributions
    sv1a_samples = sv1a_dist.sample(n_samples)
    sv1b_samples = sv1b_dist.sample(n_samples)
    sv1c_samples = sv1c_dist.sample(n_samples)
    
    # Generate states for each sample
    states = [
        {'SV1a': sv1a_samples[i], 'SV1b': sv1b_samples[i], 'SV1c': sv1c_samples[i]}
        for i in range(n_samples)
    ]
    
    # Run deterministic engine for each state
    results = batch_run(states)
    
    # Aggregate results
    decision_counts = {'ACCEPT': 0, 'COUNTER': 0, 'REJECT': 0, 'HOLD': 0}
    upls_values = []
    tripwire_values = []
    
    for result in results:
        decision_counts[result.evaluation.decision] += 1
        upls_values.append(result.scores.upls)
        tripwire_values.append(result.scores.tripwire)
    
    # Calculate statistics
    decision_proportions = {
        k: v / n_samples for k, v in decision_counts.items()
    }
    
    upls_stats = {
        'mean': float(np.mean(upls_values)),
        'std': float(np.std(upls_values)),
        'min': float(np.min(upls_values)),
        'max': float(np.max(upls_values)),
        'median': float(np.median(upls_values)),
        'percentile_5': float(np.percentile(upls_values, 5)),
        'percentile_95': float(np.percentile(upls_values, 95))
    }
    
    tripwire_stats = {
        'mean': float(np.mean(tripwire_values)),
        'std': float(np.std(tripwire_values)),
        'min': float(np.min(tripwire_values)),
        'max': float(np.max(tripwire_values)),
        'median': float(np.median(tripwire_values))
    }
    
    # Build distribution parameters
    distribution_params = {
        'sv1a': {
            'mean': float(np.mean(sv1a_samples)),
            'std': float(np.std(sv1a_samples))
        },
        'sv1b': {
            'mean': float(np.mean(sv1b_samples)),
            'std': float(np.std(sv1b_samples))
        },
        'sv1c': {
            'mean': float(np.mean(sv1c_samples)),
            'std': float(np.std(sv1c_samples))
        }
    }
    
    # Construct result
    return MonteCarloResult(
        meta={
            'n_samples': n_samples,
            'method': 'monte_carlo',
            'distributions': ['sv1a', 'sv1b', 'sv1c']
        },
        distributions=distribution_params,
        decision_frequencies=decision_counts,
        decision_proportions=decision_proportions,
        tripwire_distribution=tripwire_stats,
        upls_distribution=upls_stats
    )