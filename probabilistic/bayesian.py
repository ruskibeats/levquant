"""Bayesian Truth Decay - Time-based inference model for evidence strength.

Deterministic decay model for assessing how evidence strength changes over time.
Court-safe language only - uses likelihood terminology, not proof terminology.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp
from typing import Optional


@dataclass
class DecayAssumptions:
    """Explicit assumptions for truth decay model."""
    prior_probability: float = 0.5
    decay_rate_per_day: float = 0.02
    reference_date: Optional[str] = None
    model_version: str = "bayesian_decay_v1.0"
    disclaimer: str = (
        "This is a time-based inference model, not proof of non-existence. "
        "Decay rate is illustrative and not empirically validated."
    )


class EvidenceDecay:
    """Time-based evidence strength decay model.
    
    Uses exponential decay to model how evidentiary certainty decreases
    over time when contemporaneous records are absent.
    
    Court-safe: Uses likelihood terminology only.
    """
    
    # Court-safe inference strength labels
    INFERENCE_LABELS = {
        (0.0, 0.1): "Very low likelihood - highly improbable",
        (0.1, 0.3): "Low likelihood - improbable",
        (0.3, 0.5): "Uncertain - weak inference",
        (0.5, 0.7): "Moderate likelihood - plausible",
        (0.7, 0.9): "High likelihood - probable",
        (0.9, 1.0): "Very high likelihood - highly probable",
    }
    
    def __init__(self, assumptions: Optional[DecayAssumptions] = None):
        self.assumptions = assumptions or DecayAssumptions()
    
    def calculate_posterior(
        self,
        prior_probability: float,
        decay_rate_per_day: float,
        day_count: int,
    ) -> float:
        """Calculate posterior probability after decay.
        
        Uses exponential decay: P(t) = P(0) * exp(-λt)
        
        Args:
            prior_probability: Initial probability (0-1)
            decay_rate_per_day: Decay rate λ (default 0.02 = 2% per day)
            day_count: Days since reference event
            
        Returns:
            Posterior probability after decay
        """
        if day_count <= 0:
            return prior_probability
        
        posterior = prior_probability * exp(-decay_rate_per_day * day_count)
        return max(0.01, min(0.99, posterior))  # Bound between 1% and 99%
    
    def get_inference_label(self, probability: float) -> str:
        """Get court-safe inference label for probability."""
        for (low, high), label in self.INFERENCE_LABELS.items():
            if low <= probability < high:
                return label
        return self.INFERENCE_LABELS[(0.9, 1.0)]  # Default to highest
    
    def run_decay_analysis(
        self,
        days_since_reference: int,
        prior_probability: Optional[float] = None,
        decay_rate_per_day: Optional[float] = None,
    ) -> dict:
        """Run complete decay analysis.
        
        Args:
            days_since_reference: Days since the reference event
            prior_probability: Override default prior (0-1)
            decay_rate_per_day: Override default decay rate
            
        Returns:
            Complete decay analysis with court-safe language
        """
        prior = prior_probability if prior_probability is not None else self.assumptions.prior_probability
        decay_rate = decay_rate_per_day if decay_rate_per_day is not None else self.assumptions.decay_rate_per_day
        
        posterior = self.calculate_posterior(prior, decay_rate, days_since_reference)
        
        # Calculate time to reach threshold probabilities
        time_to_uncertain = self._calculate_time_to_threshold(prior, decay_rate, 0.5)
        time_to_low = self._calculate_time_to_threshold(prior, decay_rate, 0.2)
        
        # Generate audit hash
        audit_data = {
            "prior": prior,
            "decay_rate": decay_rate,
            "days": days_since_reference,
            "posterior": posterior,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        audit_hash = hashlib.sha256(
            json.dumps(audit_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "audit_hash": audit_hash,
            "model_version": self.assumptions.model_version,
            "assumptions": {
                "prior_probability": prior,
                "decay_rate_per_day": decay_rate,
                "days_since_reference": days_since_reference,
                "reference_date": self.assumptions.reference_date,
            },
            "results": {
                "prior_probability": prior,
                "posterior_probability": round(posterior, 4),
                "probability_decay": round(prior - posterior, 4),
                "decay_percentage": round((1 - posterior / prior) * 100, 1) if prior > 0 else 0,
                "inference_strength": self.get_inference_label(posterior),
                "days_analyzed": days_since_reference,
            },
            "projections": {
                "time_to_uncertain_days": time_to_uncertain,
                "time_to_low_likelihood_days": time_to_low,
            },
            "disclaimer": self.assumptions.disclaimer,
            "court_safe_summary": self._generate_summary(posterior, days_since_reference),
        }
    
    def _calculate_time_to_threshold(
        self,
        prior_probability: float,
        decay_rate_per_day: float,
        threshold_probability: float,
    ) -> Optional[int]:
        """Calculate days to reach threshold probability."""
        if threshold_probability >= prior_probability:
            return None
        
        # Solve: P(t) = P(0) * exp(-λt) for t
        # t = -ln(P(t)/P(0)) / λ
        import math
        days = -math.log(threshold_probability / prior_probability) / decay_rate_per_day
        return int(days) if days > 0 else None
    
    def _generate_summary(self, posterior: float, days: int) -> str:
        """Generate court-safe summary statement."""
        label = self.get_inference_label(posterior)
        
        if days < 30:
            time_frame = "recent"
        elif days < 180:
            time_frame = "moderately aged"
        else:
            time_frame = "significantly aged"
        
        return (
            f"Based on a {time_frame} record ({days} days), "
            f"the time-based inference model suggests: {label}. "
            f"This is an analytical indicator, not evidence of non-existence."
        )


def quick_decay_check(
    days_since_event: int,
    prior: float = 0.5,
    decay_rate: float = 0.02,
) -> dict:
    """Quick decay analysis without full initialization.
    
    Args:
        days_since_event: Days since reference event
        prior: Prior probability (0-1)
        decay_rate: Daily decay rate
        
    Returns:
        Simplified decay results
    """
    model = EvidenceDecay()
    return model.run_decay_analysis(days_since_event, prior, decay_rate)
