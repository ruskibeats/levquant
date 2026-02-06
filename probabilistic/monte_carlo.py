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
from scipy.stats import multivariate_normal
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


class TruncatedNormalDistribution(Distribution):
    """Truncated Normal distribution with specified bounds."""
    
    def __init__(self, mean: float, std: float, min_val: float, max_val: float):
        """
        Initialize truncated normal distribution.
        
        Args:
            mean: Mean of underlying normal distribution
            std: Standard deviation of underlying normal distribution
            min_val: Lower bound (inclusive)
            max_val: Upper bound (inclusive)
        """
        self.mean = mean
        self.std = std
        self.min_val = min_val
        self.max_val = max_val
    
    def sample(self, n: int) -> np.ndarray:
        """
        Sample from truncated normal distribution.
        
        Uses rejection sampling to enforce bounds.
        """
        samples = []
        while len(samples) < n:
            # Sample from normal
            s = np.random.normal(self.mean, self.std)
            # Accept if within bounds
            if self.min_val <= s <= self.max_val:
                samples.append(s)
        return np.array(samples)


class CorrelatedMonteCarloSampler:
    """
    Sample correlated SV parameters using multivariate normal copula.
    
    Models joint downside risk: firms with poor authority (low SV1a)
    tend to have poor procedural discipline (low SV1b).
    
    Example:
        >>> corr_matrix = np.array([
        ...     [1.0, 0.58, 0.36],  # SV1a correlations
        ...     [0.58, 1.0, 0.62],  # SV1b correlations
        ...     [0.36, 0.62, 1.0]   # SV1c correlations
        ... ])
        >>> sampler = CorrelatedMonteCarloSampler(
        ...     means=[0.38, 0.86, 0.75],
        ...     stds=[0.05, 0.03, 0.08],
        ...     corr_matrix=corr_matrix
        ... )
        >>> samples = sampler.sample(n=10000)
    """
    
    def __init__(self, means: list, stds: list, corr_matrix: np.ndarray):
        """
        Initialize correlated Monte Carlo sampler.
        
        Args:
            means: List of means [SV1a_mean, SV1b_mean, SV1c_mean]
            stds: List of standard deviations [SV1a_std, SV1b_std, SV1c_std]
            corr_matrix: 3x3 correlation matrix
        """
        self.means = np.array(means)
        self.stds = np.array(stds)
        
        # Convert correlation to covariance
        std_diag = np.diag(stds)
        self.cov_matrix = std_diag @ corr_matrix @ std_diag
    
    def sample(self, n: int) -> dict:
        """
        Sample n correlated (SV1a, SV1b, SV1c) tuples.
        
        Args:
            n: Number of samples to generate
        
        Returns:
            Dictionary with keys 'SV1a', 'SV1b', 'SV1c',
            each containing numpy array of shape (n,)
        """
        samples = multivariate_normal.rvs(
            mean=self.means,
            cov=self.cov_matrix,
            size=n
        )
        
        # Clip to [0, 1] to maintain valid SV range
        samples = np.clip(samples, 0.0, 1.0)
        
        return {
            'SV1a': samples[:, 0],
            'SV1b': samples[:, 1],
            'SV1c': samples[:, 2]
        }


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


def monte_carlo_sample_correlated(
    n_samples: int,
    means: list,
    stds: list,
    corr_matrix: np.ndarray
) -> MonteCarloResult:
    """
    Perform Monte Carlo sampling with correlated SV parameters.
    
    Uses CorrelatedMonteCarloSampler to generate joint samples,
    then runs deterministic engine and aggregates results.
    
    Args:
        n_samples: Number of Monte Carlo samples
        means: List of means [SV1a_mean, SV1b_mean, SV1c_mean]
        stds: List of standard deviations [SV1a_std, SV1b_std, SV1c_std]
        corr_matrix: 3x3 correlation matrix
    
    Returns:
        MonteCarloResult with aggregated statistics
    
    Example:
        >>> corr_matrix = np.array([
        ...     [1.0, 0.58, 0.36],
        ...     [0.58, 1.0, 0.62],
        ...     [0.36, 0.62, 1.0]
        ... ])
        >>> result = monte_carlo_sample_correlated(
        ...     n_samples=10000,
        ...     means=[0.38, 0.86, 0.75],
        ...     stds=[0.05, 0.03, 0.08],
        ...     corr_matrix=corr_matrix
        ... )
    """
    # Initialize sampler
    sampler = CorrelatedMonteCarloSampler(
        means=means,
        stds=stds,
        corr_matrix=corr_matrix
    )
    
    # Sample correlated SV parameters
    samples = sampler.sample(n_samples)
    
    # Generate states for each sample
    states = [
        {'SV1a': samples['SV1a'][i], 'SV1b': samples['SV1b'][i], 'SV1c': samples['SV1c'][i]}
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
            'mean': float(np.mean(samples['SV1a'])),
            'std': float(np.std(samples['SV1a']))
        },
        'sv1b': {
            'mean': float(np.mean(samples['SV1b'])),
            'std': float(np.std(samples['SV1b']))
        },
        'sv1c': {
            'mean': float(np.mean(samples['SV1c'])),
            'std': float(np.std(samples['SV1c']))
        }
    }
    
    # Construct result
    return MonteCarloResult(
        meta={
            'n_samples': n_samples,
            'method': 'monte_carlo_correlated',
            'distributions': ['sv1a', 'sv1b', 'sv1c'],
            'correlation': corr_matrix.tolist()
        },
        distributions=distribution_params,
        decision_frequencies=decision_counts,
        decision_proportions=decision_proportions,
        tripwire_distribution=tripwire_stats,
        upls_distribution=upls_stats
    )