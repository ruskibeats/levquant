#!/bin/bash
set -euo pipefail

echo "=== LEVQUANT FULL STACK DEMONSTRATION ==="
echo

echo "1) BASELINE DETERMINISTIC OUTPUT"
python -m cli.run --json > baseline_output.json
cat baseline_output.json
echo

echo "2) CORRELATED STRESS TEST"
python run_correlated_comparison.py
echo

echo "3) SCENARIO SWEEP"
python - <<'PY'
from scenarios.presets import PRESETS
from probabilistic.adapters import run_deterministic_engine

print('SCENARIO ANALYSIS\n' + '=' * 50)
for _, preset in PRESETS.items():
    state = preset['state']
    result = run_deterministic_engine(state=state)
    print(f"\n{preset['name']}")
    print(f"  State: SV1a={state['SV1a']:.2f}, SV1b={state['SV1b']:.2f}, SV1c={state['SV1c']:.2f}")
    print(f"  UPLS: {result.scores.upls:.3f}")
    print(f"  Decision: {result.evaluation.decision}")
    print(f"  Tripwire: {result.scores.tripwire:.2f}")
    print(f"  Confidence: {result.evaluation.confidence}")
PY

echo
echo "Done. Optional UI: streamlit run web_ui.py"