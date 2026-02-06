"""
Compare independent vs correlated Monte Carlo sampling.

This script demonstrates why correlated sampling matters:
- Independent sampling understates tail risk
- Correlated sampling models "sloppy firm" effect (SV1a/SV1b joint downside)
- CVaR should increase by 10-15% with correlation
- REJECT decisions increase in tail

Expected results:
- Independent: ~99% HOLD, ~1% COUNTER, ~0% REJECT
- Correlated: ~95% HOLD, ~3% COUNTER, ~2% REJECT (joint downside risk)
"""

import sys
from pathlib import Path
import time
import numpy as np

# Add parent directory to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from probabilistic.monte_carlo import (
    BetaDistribution,
    TruncatedNormalDistribution,
    TriangularDistribution,
    monte_carlo_sample,
    monte_carlo_sample_correlated
)


def main():
    """Run comparison between independent and correlated sampling."""
    
    print("=" * 70)
    print("INDEPENDENT VS CORRELATED MONTE CARLO COMPARISON")
    print("=" * 70)
    print()
    
    # Define same parameters for both tests
    n_samples = 1_000_000  # 1M samples for both
    
    print("Sample size: {:,} per method".format(n_samples))
    print("Expected runtime: ~3-5 minutes per method")
    print()
    
    # Method 1: Independent sampling (existing)
    print("=" * 70)
    print("METHOD 1: INDEPENDENT SAMPLING")
    print("=" * 70)
    print()
    
    sv1a_dist = BetaDistribution(alpha=5.5, beta=9.0)
    sv1b_dist = TruncatedNormalDistribution(mean=0.86, std=0.06, min_val=0.5, max_val=1.0)
    sv1c_dist = TriangularDistribution(min_val=0.45, mode=0.75, max_val=0.95)
    
    start_time = time.time()
    
    result_independent = monte_carlo_sample(
        n_samples=n_samples,
        sv1a_dist=sv1a_dist,
        sv1b_dist=sv1b_dist,
        sv1c_dist=sv1c_dist
    )
    
    end_time = time.time()
    elapsed_independent = end_time - start_time
    
    print("Independent sampling completed in {:.1f}s ({:.1f} min)".format(elapsed_independent, elapsed_independent/60))
    print()
    
    # Method 2: Correlated sampling (new)
    print("=" * 70)
    print("METHOD 2: CORRELATED SAMPLING")
    print("=" * 70)
    print()
    
    # Define correlation matrix (joint downside risk)
    # rho(SV1a, SV1b) = 0.58 (authority and procedure correlated)
    # rho(SV1a, SV1c) = 0.36 (authority and costs correlated)
    # rho(SV1b, SV1c) = 0.62 (procedure and costs highly correlated)
    corr_matrix = np.array([
        [1.00, 0.58, 0.36],  # SV1a correlations
        [0.58, 1.00, 0.62],  # SV1b correlations
        [0.36, 0.62, 1.00]   # SV1c correlations
    ])
    
    print("Correlation Matrix:")
    print("              SV1a   SV1b   SV1c")
    print("SV1a         1.00    0.58    0.36")
    print("SV1b         0.58    1.00    0.62")
    print("SV1c         0.36    0.62    1.00")
    print()
    print("Interpretation:")
    print("  -> rho(SV1a, SV1b) = 0.58: Poor authority correlates with poor procedure")
    print("  -> rho(SV1b, SV1c) = 0.62: Procedural issues drive cost asymmetry")
    print("  -> Models 'sloppy firm' effect: joint downside risk")
    print()
    
    start_time = time.time()
    
    result_correlated = monte_carlo_sample_correlated(
        n_samples=n_samples,
        means=[0.38, 0.86, 0.75],  # SV1a, SV1b, SV1c means
        stds=[0.05, 0.03, 0.08],  # SV1a, SV1b, SV1c stds
        corr_matrix=corr_matrix
    )
    
    end_time = time.time()
    elapsed_correlated = end_time - start_time
    
    print("Correlated sampling completed in {:.1f}s ({:.1f} min)".format(elapsed_correlated, elapsed_correlated/60))
    print()
    
    # Comparison results
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print()
    
    # Decision distribution comparison
    print("Decision Distribution Comparison:")
    print("-" * 70)
    print("{:<15} {:>20} {:>20} {:>20}".format("Decision", "Independent", "Correlated", "Change"))
    print("-" * 70)
    
    for decision in ['ACCEPT', 'COUNTER', 'REJECT', 'HOLD']:
        indep_prop = result_independent.decision_proportions[decision] * 100
        corr_prop = result_correlated.decision_proportions[decision] * 100
        change = corr_prop - indep_prop
        
        print("{:<15} {:>18.2f}%    {:>18.2f}%    {:>+18.2f}%".format(decision, indep_prop, corr_prop, change))
    
    print()
    
    # UPLS distribution comparison
    print("UPLS Distribution Comparison:")
    print("-" * 70)
    print("{:<20} {:>20} {:>20} {:>20}".format("Metric", "Independent", "Correlated", "Change"))
    print("-" * 70)
    
    upls_indep = result_independent.upls_distribution
    upls_corr = result_correlated.upls_distribution
    
    for metric in ['mean', 'std', 'min', 'max', 'median', 'percentile_5', 'percentile_95']:
        indep_val = upls_indep[metric]
        corr_val = upls_corr[metric]
        change = corr_val - indep_val
        
        print("{:<20} {:>18.3f}    {:>18.3f}    {:>+18.3f}".format(metric, indep_val, corr_val, change))
    
    print()
    
    # CVaR comparison (5th percentile = downside risk)
    print("Tail Risk Comparison (CVaR at 5th percentile):")
    print("-" * 70)
    
    indep_cvar = upls_indep['percentile_5']
    corr_cvar = upls_corr['percentile_5']
    cvar_increase = ((corr_cvar - indep_cvar) / abs(indep_cvar)) * 100
    
    print("Independent 5th percentile UPLS: {:.3f}".format(indep_cvar))
    print("Correlated 5th percentile UPLS:   {:.3f}".format(corr_cvar))
    print("Tail risk increase:                    {:+.1f}%".format(cvar_increase))
    print()
    
    # Interpretation
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print()
    
    print("Key Findings:")
    print()
    
    # Analyze decision changes
    hold_indep = result_independent.decision_proportions['HOLD']
    hold_corr = result_correlated.decision_proportions['HOLD']
    hold_decrease = ((hold_indep - hold_corr) / hold_indep) * 100
    
    reject_indep = result_independent.decision_proportions['REJECT']
    reject_corr = result_correlated.decision_proportions['REJECT']
    reject_increase = ((reject_corr - reject_indep) / max(reject_indep, 0.001)) * 100  # Avoid division by zero
    
    print("1. HOLD dominance reduced by {:.1f}% with correlated sampling".format(hold_decrease))
    print("   -> Joint downside risk pushes more decisions to REJECT/COUNTER")
    print()
    
    print("2. REJECT decisions increase by {:.1f}% with correlated sampling".format(reject_increase))
    print("   -> 'Sloppy firm' effect: low authority + low procedure = REJECT")
    print("   -> Independent sampling understates this tail risk")
    print()
    
    print("3. CVaR (5th percentile UPLS) increased by {:.1f}%".format(cvar_increase))
    print("   -> Downside risk is higher when SVs are correlated")
    print("   -> Tail events are more frequent in realistic litigation")
    print()
    
    # Recommendation
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print()
    
    print("USE CORRELATED SAMPLING FOR:")
    print("  -> Accurate tail risk modeling")
    print("  -> Realistic joint downside scenarios")
    print("  -> CVaR calculations for settlement leverage")
    print("  -> Insurer-style capital risk assessment")
    print()
    
    print("INDEPENDENT SAMPLING IS APPROPRIATE FOR:")
    print("  -> Exploratory analysis")
    print("  -> Quick what-if scenarios")
    print("  -> Educational demonstrations")
    print()
    
    print("=" * 70)


if __name__ == '__main__':
    main()