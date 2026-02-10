"""
Monte Carlo sampling for probabilistic extensions.

This file provides distribution sampling and aggregation on top of the
deterministic engine. It does not import from /engine.

Critical Design Principle:
    Use probabilistic.adapters.run_deterministic_engine() to get results.
    Never import from /engine directly.

Status: v2.1-enhanced (with seed, convergence, worst-case tracking)
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import multivariate_normal
from probabilistic.adapters import run_deterministic_engine, batch_run
from probabilistic.schemas import MonteCarloResult


class Distribution:
    """Base class for probability distributions."""
    
    def sample(self, n: int) -> np.ndarray:
        """Generate n samples from this distribution."""
        raise NotImplementedError("Subclasses must implement sample()")


class UniformDistribution(Distribution):
    """Uniform distribution between min and max."""
    
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val
    
    def sample(self, n: int) -> np.ndarray:
        return np.random.uniform(self.min_val, self.max_val, size=n)


class NormalDistribution(Distribution):
    """Normal (Gaussian) distribution with clipping to [0, 1]."""
    
    def __init__(self, mean: float, std: float):
        self.mean = mean
        self.std = std
    
    def sample(self, n: int) -> np.ndarray:
        samples = np.random.normal(self.mean, self.std, size=n)
        return np.clip(samples, 0.0, 1.0)


class BetaDistribution(Distribution):
    """Beta distribution (useful for bounded [0, 1] variables)."""
    
    def __init__(self, alpha: float, beta: float):
        self.alpha = alpha
        self.beta = beta
    
    def sample(self, n: int) -> np.ndarray:
        return np.random.beta(self.alpha, self.beta, size=n)


class TriangularDistribution(Distribution):
    """Triangular distribution with min, mode, max."""
    
    def __init__(self, min_val: float, mode: float, max_val: float):
        self.min_val = min_val
        self.mode = mode
        self.max_val = max_val
    
    def sample(self, n: int) -> np.ndarray:
        return np.random.triangular(self.min_val, self.mode, self.max_val, size=n)


class TruncatedNormalDistribution(Distribution):
    """Truncated Normal distribution with specified bounds."""
    
    def __init__(self, mean: float, std: float, min_val: float, max_val: float):
        self.mean = mean
        self.std = std
        self.min_val = min_val
        self.max_val = max_val
    
    def sample(self, n: int) -> np.ndarray:
        samples = []
        while len(samples) < n:
            s = np.random.normal(self.mean, self.std)
            if self.min_val <= s <= self.max_val:
                samples.append(s)
        return np.array(samples)


class CorrelatedMonteCarloSampler:
    """Sample correlated SV parameters using multivariate normal copula."""
    
    def __init__(self, means: list, stds: list, corr_matrix: np.ndarray):
        self.means = np.array(means)
        self.stds = np.array(stds)
        std_diag = np.diag(stds)
        self.cov_matrix = std_diag @ corr_matrix @ std_diag
    
    def sample(self, n: int) -> dict:
        samples = multivariate_normal.rvs(mean=self.means, cov=self.cov_matrix, size=n)
        samples = np.clip(samples, 0.0, 1.0)
        return {'SV1a': samples[:, 0], 'SV1b': samples[:, 1], 'SV1c': samples[:, 2]}


def _track_convergence(upls_values: list, tripwire_values: list, batch_size: int = 1000) -> dict:
    """
    Track convergence metrics over batches.
    
    Args:
        upls_values: List of UPLS values from all samples
        tripwire_values: List of tripwire values from all samples
        batch_size: Size of each batch for convergence tracking
        
    Returns:
        Dictionary with convergence metrics
    """
    n_total = len(upls_values)
    n_batches = n_total // batch_size
    
    if n_batches < 2:
        return {
            'converged': False,
            'sem_upls': float(np.std(upls_values) / np.sqrt(n_total)),
            'sem_tripwire': float(np.std(tripwire_values) / np.sqrt(n_total)),
            'batch_means_upls': [],
            'batch_means_tripwire': []
        }
    
    batch_means_upls = []
    batch_means_tripwire = []
    
    for i in range(n_batches):
        start_idx = i * batch_size
        end_idx = start_idx + batch_size
        batch_means_upls.append(np.mean(upls_values[start_idx:end_idx]))
        batch_means_tripwire.append(np.mean(tripwire_values[start_idx:end_idx]))
    
    # Calculate standard error of the mean
    sem_upls = np.std(upls_values) / np.sqrt(n_total)
    sem_tripwire = np.std(tripwire_values) / np.sqrt(n_total)
    
    # Check convergence: coefficient of variation of batch means < 5%
    cv_upls = np.std(batch_means_upls) / np.mean(batch_means_upls) if np.mean(batch_means_upls) > 0 else 0
    converged = cv_upls < 0.05
    
    return {
        'converged': converged,
        'sem_upls': float(sem_upls),
        'sem_tripwire': float(sem_tripwire),
        'batch_means_upls': [float(x) for x in batch_means_upls],
        'batch_means_tripwire': [float(x) for x in batch_means_tripwire],
        'cv_upls': float(cv_upls)
    }


def _identify_worst_cases(
    results: list,
    sv1a_samples: np.ndarray,
    sv1b_samples: np.ndarray,
    sv1c_samples: np.ndarray,
    n_worst: int = 5
) -> list:
    """
    Identify worst-case scenarios (lowest UPLS, highest tripwire).
    
    Args:
        results: List of deterministic engine results
        sv1a_samples: SV1a values for each sample
        sv1b_samples: SV1b values for each sample
        sv1c_samples: SV1c values for each sample
        n_worst: Number of worst cases to identify
        
    Returns:
        List of worst-case scenarios with details
    """
    # Combine results with their inputs
    scenarios = []
    for i, result in enumerate(results):
        scenarios.append({
            'index': i,
            'upls': result.scores.upls,
            'tripwire': result.scores.tripwire,
            'decision': result.evaluation.decision,
            'sv1a': float(sv1a_samples[i]),
            'sv1b': float(sv1b_samples[i]),
            'sv1c': float(sv1c_samples[i])
        })
    
    # Sort by UPLS (ascending - worst is lowest)
    worst_by_upls = sorted(scenarios, key=lambda x: x['upls'])[:n_worst]
    
    # Sort by tripwire (descending - worst is highest)
    worst_by_tripwire = sorted(scenarios, key=lambda x: x['tripwire'], reverse=True)[:n_worst]
    
    return {
        'lowest_upls': worst_by_upls,
        'highest_tripwire': worst_by_tripwire
    }


def monte_carlo_sample(
    n_samples: int,
    sv1a_dist: Distribution,
    sv1b_dist: Distribution,
    sv1c_dist: Distribution,
    seed: Optional[int] = None,
    track_convergence: bool = True
) -> MonteCarloResult:
    """
    Perform Monte Carlo sampling over SV parameters with enhanced features.
    
    Args:
        n_samples: Number of Monte Carlo samples
        sv1a_dist: Distribution for SV1a
        sv1b_dist: Distribution for SV1b
        sv1c_dist: Distribution for SV1c
        seed: Random seed for reproducibility (optional)
        track_convergence: Whether to track convergence metrics
    
    Returns:
        MonteCarloResult with aggregated statistics, convergence metrics, and worst-case scenarios
    """
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
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
    decision_proportions = {k: v / n_samples for k, v in decision_counts.items()}
    
    upls_stats = {
        'mean': float(np.mean(upls_values)),
        'std': float(np.std(upls_values)),
        'min': float(np.min(upls_values)),
        'max': float(np.max(upls_values)),
        'median': float(np.median(upls_values)),
        'percentile_5': float(np.percentile(upls_values, 5)),
        'percentile_95': float(np.percentile(upls_values, 95)),
        'samples': upls_values  # Raw samples for histogram
    }
    
    tripwire_stats = {
        'mean': float(np.mean(tripwire_values)),
        'std': float(np.std(tripwire_values)),
        'min': float(np.min(tripwire_values)),
        'max': float(np.max(tripwire_values)),
        'median': float(np.median(tripwire_values)),
        'samples': tripwire_values  # Raw samples for histogram
    }
    
    # Track convergence
    convergence_metrics = None
    if track_convergence and n_samples >= 1000:
        convergence_metrics = _track_convergence(upls_values, tripwire_values)
    
    # Identify worst-case scenarios
    worst_cases = _identify_worst_cases(
        results, sv1a_samples, sv1b_samples, sv1c_samples
    )
    
    # Build distribution parameters
    distribution_params = {
        'sv1a': {'mean': float(np.mean(sv1a_samples)), 'std': float(np.std(sv1a_samples))},
        'sv1b': {'mean': float(np.mean(sv1b_samples)), 'std': float(np.std(sv1b_samples))},
        'sv1c': {'mean': float(np.mean(sv1c_samples)), 'std': float(np.std(sv1c_samples))}
    }
    
    # Build metadata
    meta = {
        'n_samples': n_samples,
        'method': 'monte_carlo',
        'distributions': ['sv1a', 'sv1b', 'sv1c'],
        'seed': seed,
        'convergence': convergence_metrics,
        'worst_cases': worst_cases
    }
    
    return MonteCarloResult(
        meta=meta,
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
    corr_matrix: np.ndarray,
    seed: Optional[int] = None,
    track_convergence: bool = True
) -> MonteCarloResult:
    """
    Perform Monte Carlo sampling with correlated SV parameters.
    
    Args:
        n_samples: Number of Monte Carlo samples
        means: List of means [SV1a_mean, SV1b_mean, SV1c_mean]
        stds: List of standard deviations [SV1a_std, SV1b_std, SV1c_std]
        corr_matrix: 3x3 correlation matrix
        seed: Random seed for reproducibility (optional)
        track_convergence: Whether to track convergence metrics
    
    Returns:
        MonteCarloResult with aggregated statistics, convergence metrics, and worst-case scenarios
    """
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    # Initialize sampler
    sampler = CorrelatedMonteCarloSampler(means=means, stds=stds, corr_matrix=corr_matrix)
    
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
    decision_proportions = {k: v / n_samples for k, v in decision_counts.items()}
    
    upls_stats = {
        'mean': float(np.mean(upls_values)),
        'std': float(np.std(upls_values)),
        'min': float(np.min(upls_values)),
        'max': float(np.max(upls_values)),
        'median': float(np.median(upls_values)),
        'percentile_5': float(np.percentile(upls_values, 5)),
        'percentile_95': float(np.percentile(upls_values, 95)),
        'samples': upls_values
    }
    
    tripwire_stats = {
        'mean': float(np.mean(tripwire_values)),
        'std': float(np.std(tripwire_values)),
        'min': float(np.min(tripwire_values)),
        'max': float(np.max(tripwire_values)),
        'median': float(np.median(tripwire_values)),
        'samples': tripwire_values
    }
    
    # Track convergence
    convergence_metrics = None
    if track_convergence and n_samples >= 1000:
        convergence_metrics = _track_convergence(upls_values, tripwire_values)
    
    # Identify worst-case scenarios
    worst_cases = _identify_worst_cases(
        results, samples['SV1a'], samples['SV1b'], samples['SV1c']
    )
    
    # Build distribution parameters
    distribution_params = {
        'sv1a': {'mean': float(np.mean(samples['SV1a'])), 'std': float(np.std(samples['SV1a']))},
        'sv1b': {'mean': float(np.mean(samples['SV1b'])), 'std': float(np.std(samples['SV1b']))},
        'sv1c': {'mean': float(np.mean(samples['SV1c'])), 'std': float(np.std(samples['SV1c']))}
    }
    
    # Build metadata
    meta = {
        'n_samples': n_samples,
        'method': 'monte_carlo_correlated',
        'distributions': ['sv1a', 'sv1b', 'sv1c'],
        'correlation': corr_matrix.tolist(),
        'seed': seed,
        'convergence': convergence_metrics,
        'worst_cases': worst_cases
    }
    
    return MonteCarloResult(
        meta=meta,
        distributions=distribution_params,
        decision_frequencies=decision_counts,
        decision_proportions=decision_proportions,
        tripwire_distribution=tripwire_stats,
        upls_distribution=upls_stats
    )
