# LEVQUANT INPUT BUILDER v1.1 (Compact)

Convert evidence into LEVQUANT-importable JSON.

## Output Format
```json
{
  "inputs": {
    "procedural": {"SV1a": 0.0-1.0, "SV1b": 0.0-1.0, "SV1c": 0.0-1.0},
    "monetary": {
      "principal_debt_gbp": number, "claimant_costs_gbp": number,
      "defendant_costs_estimate_gbp": number, "regulatory_exposure_gbp": number,
      "transaction_value_gbp": number, "assumptions_notes": "string"
    },
    "kill_switches": {
      "nullity_confirmed": boolean, "regulatory_open": boolean,
      "insurer_notice": boolean, "override_admitted": boolean, "shadow_director": boolean
    },
    "fear_override": 0.0-1.0,
    "containment": {
      "containment_exposure_gbp": number, "reputational_damage_gbp": number,
      "regulatory_fine_risk_gbp": number, "litigation_cascade_risk_gbp": number
    },
    "stance": {"anchor_gbp": number, "minimum_objective_gbp": number, "objective_mode": "standard|containment|anchor_driven"}
  },
  "evidence_map": {},
  "audit": {"timestamp_utc": "ISO8601", "builder_version": "v1.1", "warnings": [], "missing_required_evidence": []}
}
```

## Rules
1. Use ONLY provided evidence. No invention.
2. Court-safe: "alleged/supported/inferred", never "proven".
3. Valid JSON only — no markdown, no commentary.
4. Unsupported fields: use defaults (SVs=0.50, money=0, kill_switches=false, fear=0.50, mode="containment") and list in audit.warnings.

## Calibration
- **SV1a**: claim validity (standing, jurisdiction, deadlines)
- **SV1b**: rule-breaking leverage (irregularity, override, regulator attention)
- **SV1c**: cost pressure (urgent deadlines, adverse costs, insurer involvement)
- **Kill switches**: true ONLY if explicitly evidenced
- **Fear**: 0.3-0.5 internal, 0.6-0.8 existential risk, 0.9-1.0 external escalation
- **Containment**: quantified exposure only; else 0

## Context
[PASTE EVIDENCE BUNDLE HERE]

Return ONLY the JSON object.
