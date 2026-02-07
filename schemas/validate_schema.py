"""Validate CLI JSON output against schema expectations used in CI."""

import json
import sys
from pathlib import Path


def _fail(message: str) -> None:
    print(f"Error: {message}")
    sys.exit(1)


def validate() -> None:
    output_file = Path("/tmp/output.json")

    if not output_file.exists():
        _fail("/tmp/output.json not found")

    try:
        with output_file.open() as f:
            data = json.load(f)
    except Exception as exc:
        _fail(f"failed to parse JSON: {exc}")

    required = ["inputs", "scores", "evaluation", "interpretation", "version"]
    missing = [key for key in required if key not in data]
    if missing:
        _fail(f"missing keys: {missing}")

    for sv in ["SV1a", "SV1b", "SV1c"]:
        if sv not in data["inputs"]:
            _fail(f"missing input {sv}")

        value = data["inputs"][sv]
        if not isinstance(value, (int, float)):
            _fail(f"{sv} must be numeric, got {type(value).__name__}")

        if not (0.0 <= float(value) <= 1.0):
            _fail(f"{sv}={value} out of range [0,1]")

    print("✓ Schema validation passed")


if __name__ == "__main__":
    validate()