"""
Run 250,000 Monte Carlo simulations.

This script demonstrates the probabilistic extensions by running
a large-scale Monte Carlo analysis on the deterministic engine.
"""

import time
from probabilistic.monte_carlo import NormalDistribution, monte_carlo_sample


def main():
    """Run 250,000 Monte Carlo simulations."""
    
    print("=" * 60)
    print("MONTE CARLO SIMULATION - 250,000 SAMPLES")
    print("=" * 60)
    print()
    
    # Define distributions for SV parameters
    # These are example distributions - adjust based on case specifics
    print("Defining SV parameter distributions:")
    print("  SV1a (Claim Validity): Normal(μ=0.38, σ=0.05)")
    print("  SV1b (Procedural Advantage): Normal(μ=0.86, σ=0.03)")
    print("  SV1c (Cost Asymmetry): Normal(μ=0.75, σ=0.08)")
    print()
    
    sv1a_dist = NormalDistribution(mean=0.38, std=0.05)
    sv1b_dist = NormalDistribution(mean=0.86, std=0.03)
    sv1c_dist = NormalDistribution(mean=0.75, std=0.08)
    
    # Run Monte Carlo simulation
    print(f"Running {250_000:,} Monte Carlo samples...")
    print("This may take 30-60 seconds...")
    print()
    
    start_time = time.time()
    
    result = monte_carlo_sample(
        n_samples=250_000,
        sv1a_dist=sv1a_dist,
        sv1b_dist=sv1b_dist,
        sv1c_dist=sv1c_dist
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Display results
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()
    
    print(f"Simulation completed in {elapsed_time:.2f} seconds")
    print(f"Samples per second: {250_000 / elapsed_time:.0f}")
    print()
    
    print("Decision Distribution:")
    print("-" * 40)
    total_decisions = sum(result.decision_frequencies.values())
    for decision in ['ACCEPT', 'COUNTER', 'HOLD', 'REJECT']:
        freq = result.decision_frequencies[decision]
        prop = result.decision_proportions[decision]
        print(f"  {decision:10s}: {freq:6,} ({prop*100:.2f}%)")
    print()
    
    print("UPLS Distribution:")
    print("-" * 40)
    upls = result.upls_distribution
    print(f"  Mean:     {upls['mean']:.3f}")
    print(f"  Std Dev:  {upls['std']:.3f}")
    print(f"  Median:   {upls['median']:.3f}")
    print(f"  Min:      {upls['min']:.3f}")
    print(f"  Max:      {upls['max']:.3f}")
    print(f"  5th %ile: {upls['percentile_5']:.3f}")
    print(f"  95th %ile:{upls['percentile_95']:.3f}")
    print()
    
    print("Tripwire Distribution:")
    print("-" * 40)
    tripwire = result.tripwire_distribution
    print(f"  Mean:     {tripwire['mean']:.2f}")
    print(f"  Std Dev:  {tripwire['std']:.2f}")
    print(f"  Median:   {tripwire['median']:.2f}")
    print(f"  Min:      {tripwire['min']:.2f}")
    print(f"  Max:      {tripwire['max']:.2f}")
    print()
    
    print("SV Distribution Parameters:")
    print("-" * 40)
    for sv_name in ['sv1a', 'sv1b', 'sv1c']:
        params = result.distributions[sv_name]
        print(f"  {sv_name.upper()}:")
        print(f"    Mean: {params['mean']:.3f}")
        print(f"    Std:  {params['std']:.3f}")
    print()
    
    print("=" * 60)


if __name__ == '__main__':
    main()