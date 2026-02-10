"""
Pydantic schemas for CLI JSON contracts.

This file defines type-safe models for consuming deterministic engine output.
These models validate JSON structure and provide IDE autocomplete for probabilistic code.

Critical Design Principle:
    These schemas consume CLI JSON output.
    They do not import from /engine.
"""

from typing import Dict, Any, List, Union
from pydantic import BaseModel, Field, validator


class Inputs(BaseModel):
    """Input state from deterministic engine."""
    
    SV1a: float = Field(..., ge=0.0, le=1.0, description="Claim validity strength")
    SV1b: float = Field(..., ge=0.0, le=1.0, description="Procedural advantage")
    SV1c: float = Field(..., ge=0.0, le=1.0, description="Cost asymmetry")


class Scores(BaseModel):
    """Scores from deterministic engine."""
    
    upls: float = Field(..., ge=0.0, le=1.0, description="Unified Procedural Leverage Score")
    tripwire: float = Field(..., ge=0.0, le=10.0, description="Tripwire score")


class Evaluation(BaseModel):
    """Evaluation from deterministic engine."""
    
    decision: str = Field(..., description="Recommended action (ACCEPT, COUNTER, REJECT, HOLD)")
    confidence: str = Field(..., description="Confidence level (Very Low, Low, Moderate, Good, Strong)")
    tripwire_triggered: bool = Field(..., description="Whether tripwire threshold exceeded")
    upls_value: float = Field(..., ge=0.0, le=1.0, description="UPLS value (duplicate for convenience)")
    tripwire_value: float = Field(..., ge=0.0, le=10.0, description="Tripwire value (duplicate for convenience)")
    
    @validator('decision')
    def validate_decision(cls, v):
        valid_decisions = {'ACCEPT', 'COUNTER', 'REJECT', 'HOLD'}
        if v not in valid_decisions:
            raise ValueError(f"Invalid decision: {v}. Must be one of {valid_decisions}")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        valid_confidences = {'Very Low', 'Low', 'Moderate', 'Good', 'Strong'}
        if v not in valid_confidences:
            raise ValueError(f"Invalid confidence: {v}. Must be one of {valid_confidences}")
        return v


class Interpretation(BaseModel):
    """Interpretation from deterministic engine."""
    
    leverage_position: str = Field(..., description="Human-readable leverage description")
    decision_explanation: str = Field(..., description="Human-readable decision explanation")
    tripwire_status: str = Field(..., description="Human-readable tripwire status")
    confidence_explanation: str = Field(..., description="Human-readable confidence explanation")


class DeterministicOutput(BaseModel):
    """Complete output from deterministic engine (CLI JSON schema)."""
    
    inputs: Inputs
    scores: Scores
    evaluation: Evaluation
    interpretation: Interpretation
    version: str = Field(..., description="Engine version")
    
    @validator('version')
    def validate_version(cls, v):
        if not v.startswith(('1.', '2.')):
            raise ValueError(f"Unexpected version: {v}. Expected 1.x or 2.x")
        return v
    
    class Config:
        """Pydantic configuration."""
        extra = 'allow'


class DistributionStats(BaseModel):
    """Statistics for a distribution including raw samples."""
    
    mean: float
    std: float
    min: float
    max: float
    median: float
    samples: List[float] = Field(default_factory=list, description="Raw samples for histogram")
    
    class Config:
        extra = 'allow'


class UPLSDistribution(BaseModel):
    """UPLS distribution with percentiles and samples."""
    
    mean: float
    std: float
    min: float
    max: float
    median: float
    percentile_5: float
    percentile_95: float
    samples: List[float] = Field(default_factory=list, description="Raw samples for histogram")
    
    class Config:
        extra = 'allow'


class TripwireDistribution(BaseModel):
    """Tripwire distribution statistics with samples."""
    
    mean: float
    std: float
    min: float
    max: float
    median: float
    samples: List[float] = Field(default_factory=list, description="Raw samples for histogram")
    
    class Config:
        extra = 'allow'


class MonteCarloResult(BaseModel):
    """Result from Monte Carlo sampling (probabilistic layer)."""
    
    meta: Dict[str, Any] = Field(..., description="Metadata (n_samples, method, seed, convergence, worst_cases)")
    distributions: Dict[str, Dict[str, float]] = Field(..., description="SV distribution parameters")
    decision_frequencies: Dict[str, int] = Field(..., description="Decision frequency counts")
    decision_proportions: Dict[str, float] = Field(..., description="Decision probability estimates")
    tripwire_distribution: Dict[str, Any] = Field(..., description="Tripwire distribution statistics (includes samples)")
    upls_distribution: Dict[str, Any] = Field(..., description="UPLS distribution statistics (includes samples)")
    
    class Config:
        extra = 'allow'


class ScenarioResult(BaseModel):
    """Result from named scenario execution."""
    
    scenario_name: str = Field(..., description="Name of scenario run")
    description: str = Field(..., description="Scenario description")
    output: DeterministicOutput = Field(..., description="Deterministic engine output")
    
    class Config:
        extra = 'allow'
