"""
Validate CLI JSON output against Pydantic schema.

This script validates that the current engine output matches
the expected schema contract defined in probabilistic.schemas.

Usage:
    python schemas/validate_schema.py
"""

import json
from pathlib import Path
from probabilistic.schemas import DeterministicOutput


def validate_engine_output():
    """Validate schemas/engine_output.json against DeterministicOutput schema."""
    
    schema_path = Path(__file__).parent / "engine_output.json"
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        return False
    
    print(f"Validating schema: {schema_path}")
    print()
    
    # Load JSON
    with open(schema_path) as f:
        data = json.load(f)
    
    print("Loaded JSON with keys:")
    for key in sorted(data.keys()):
        print(f"  - {key}")
    print()
    
    # Validate against Pydantic model
    try:
        output = DeterministicOutput(**data)
        print("✅ Schema validation PASSED")
        print()
        print("Validated fields:")
        print(f"  - inputs: SV1a={output.inputs.SV1a}, SV1b={output.inputs.SV1b}, SV1c={output.inputs.SV1c}")
        print(f"  - scores: upls={output.scores.upls}, tripwire={output.scores.tripwire}")
        print(f"  - evaluation: decision={output.evaluation.decision}, confidence={output.evaluation.confidence}")
        print(f"  - version: {output.version}")
        print()
        return True
    
    except Exception as e:
        print("❌ Schema validation FAILED")
        print(f"Error: {e}")
        print()
        return False


if __name__ == '__main__':
    success = validate_engine_output()
    exit(0 if success else 1)