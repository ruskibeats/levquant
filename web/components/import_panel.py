"""Import JSON panel for loading saved runs into the dashboard.

Supports two formats:
1. full_run.json format (exported from dashboard)
2. Calibration output format (from NotebookLM/LLM)
"""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from decision_support.schemas import (
    ContainmentInputs,
    KillSwitchInputs,
    MonetaryInputs,
    NegotiationStance,
    ProceduralInputs,
)


def _detect_json_format(data: dict) -> str:
    """Detect which JSON format we're dealing with.
    
    Returns:
        "full_run" | "calibration_output" | "unknown"
    """
    # Check for full_run format
    if "inputs" in data and "procedural" in data.get("inputs", {}):
        return "full_run"
    
    # Check for calibration output format
    if "engine_snapshot" in data and "inputs" in data.get("engine_snapshot", {}):
        return "calibration_output"
    
    return "unknown"


def validate_imported_json(data: dict) -> tuple[bool, str, str]:
    """Validate that imported JSON has required structure.
    
    Returns:
        Tuple of (is_valid, error_message, json_format)
    """
    json_format = _detect_json_format(data)
    
    if json_format == "unknown":
        return False, "Unrecognized JSON format. Expected full_run.json or calibration output.", json_format
    
    if json_format == "full_run":
        inputs = data.get("inputs", {})
        if "procedural" not in inputs:
            return False, "Missing inputs.procedural", json_format
        proc = inputs["procedural"]
        if not all(k in proc for k in ["SV1a", "SV1b", "SV1c"]):
            return False, "Missing SV1a/SV1b/SV1c in procedural inputs", json_format
    
    elif json_format == "calibration_output":
        engine_snapshot = data.get("engine_snapshot", {})
        inputs = engine_snapshot.get("inputs", {})
        if not all(k in inputs for k in ["SV1a", "SV1b", "SV1c"]):
            return False, "Missing SV1a/SV1b/SV1c in engine_snapshot.inputs", json_format
    
    return True, "Valid", json_format


def extract_inputs_from_json(data: dict, json_format: str) -> dict:
    """Extract input values from imported JSON.
    
    Handles both full_run and calibration_output formats.
    
    Returns dict with keys: procedural, monetary, kill_switches, 
    containment, stance, fear_override
    """
    if json_format == "calibration_output":
        return _extract_from_calibration_output(data)
    else:
        return _extract_from_full_run(data)


def _extract_from_calibration_output(data: dict) -> dict:
    """Extract inputs from calibration output format.
    
    Calibration output has engine_snapshot.inputs but may not have
    full monetary/kill_switch data. Uses defaults where missing.
    """
    engine_snapshot = data.get("engine_snapshot", {})
    inputs = engine_snapshot.get("inputs", {})
    
    # Procedural inputs from engine_snapshot.inputs
    procedural = ProceduralInputs(
        SV1a=inputs.get("SV1a", 0.38),
        SV1b=inputs.get("SV1b", 0.86),
        SV1c=inputs.get("SV1c", 0.75),
    )
    
    # Try to extract from fact_checks for kill switches
    kill_switches = _infer_kill_switches_from_calibration(data)
    
    # Try to extract monetary from fact_checks or use defaults
    monetary = _infer_monetary_from_calibration(data)
    
    # Containment - use defaults (calibration output doesn't have this)
    containment = ContainmentInputs(
        containment_exposure_gbp=0.0,
        reputational_damage_gbp=0.0,
        regulatory_fine_risk_gbp=0.0,
        litigation_cascade_risk_gbp=0.0,
    )
    
    # Stance from settlement_corridor_check if available
    corridor_check = data.get("settlement_corridor_check", {})
    stance = NegotiationStance(
        anchor_gbp=corridor_check.get("anchor_gbp", 15_000_000.0),
        minimum_objective_gbp=corridor_check.get("minimum_objective_gbp", 9_000_000.0),
        objective_mode="standard",  # Default, not in calibration output
    )
    
    # Fear override - not in calibration output
    fear_override = None
    
    return {
        "procedural": procedural,
        "monetary": monetary,
        "kill_switches": kill_switches,
        "containment": containment,
        "stance": stance,
        "fear_override": fear_override,
    }


def _infer_kill_switches_from_calibration(data: dict) -> KillSwitchInputs:
    """Infer kill switch states from calibration output fact_checks."""
    fact_checks = data.get("fact_checks", [])
    
    # Look for evidence of kill switch conditions in fact checks
    nullity_confirmed = False
    regulatory_open = False
    insurer_notice = False
    override_admitted = False
    shadow_director = False
    
    for fact in fact_checks:
        claim = fact.get("claim", "").lower()
        status = fact.get("status", "").upper()
        
        # Check for defence nullity
        if "defence" in claim and ("nullity" in claim or "not received" in claim or "not filed" in claim):
            if status in ["PROVEN", "EVIDENCED"]:
                nullity_confirmed = True
        
        # Check for regulatory investigation
        if any(kw in claim for kw in ["sra", "regulatory", "investigation"]):
            if status in ["PROVEN", "EVIDENCED"]:
                regulatory_open = True
        
        # Check for insurer notification
        if any(kw in claim for kw in ["insurer", "insurance", "void", "exclusion"]):
            if status in ["PROVEN", "EVIDENCED"]:
                insurer_notice = True
        
        # Check for administrative override
        if any(kw in claim for kw in ["override", "backdoor", "administrative"]):
            if status in ["PROVEN", "EVIDENCED"]:
                override_admitted = True
        
        # Check for shadow director
        if any(kw in claim for kw in ["shadow", "director", "maven", "patel"]):
            if status in ["PROVEN", "EVIDENCED", "INFERRED"]:
                shadow_director = True
    
    return KillSwitchInputs(
        nullity_confirmed=nullity_confirmed,
        regulatory_open=regulatory_open,
        insurer_notice=insurer_notice,
        override_admitted=override_admitted,
        shadow_director=shadow_director,
    )


def _infer_monetary_from_calibration(data: dict) -> MonetaryInputs:
    """Infer monetary inputs from calibration output."""
    # Try to get from settlement corridor check
    corridor = data.get("settlement_corridor_check", {})
    anchor = corridor.get("anchor_gbp", 15_000_000.0)
    minimum = corridor.get("minimum_objective_gbp", 9_000_000.0)
    
    # Default monetary values - calibration output doesn't have detailed monetary
    return MonetaryInputs(
        principal_debt_gbp=0.0,
        claimant_costs_gbp=0.0,
        defendant_costs_estimate_gbp=0.0,
        regulatory_exposure_gbp=0.0,
        transaction_value_gbp=0.0,
        assumptions_notes=f"Imported from calibration output. Anchor: £{anchor:,.0f}, Minimum: £{minimum:,.0f}",
    )


def _extract_from_full_run(data: dict) -> dict:
    """Extract inputs from full_run.json format."""
    inputs = data.get("inputs", {})
    
    # Procedural inputs
    proc_data = inputs.get("procedural", {})
    procedural = ProceduralInputs(
        SV1a=proc_data.get("SV1a", 0.38),
        SV1b=proc_data.get("SV1b", 0.86),
        SV1c=proc_data.get("SV1c", 0.75),
    )
    
    # Monetary inputs
    money_data = inputs.get("monetary", {})
    monetary = MonetaryInputs(
        principal_debt_gbp=money_data.get("principal_debt_gbp", 0.0),
        claimant_costs_gbp=money_data.get("claimant_costs_gbp", 0.0),
        defendant_costs_estimate_gbp=money_data.get("defendant_costs_estimate_gbp", 0.0),
        regulatory_exposure_gbp=money_data.get("regulatory_exposure_gbp", 0.0),
        transaction_value_gbp=money_data.get("transaction_value_gbp", 0.0),
        assumptions_notes=money_data.get("assumptions_notes", ""),
    )
    
    # Kill switches
    kill_data = inputs.get("kill_switches", {})
    kill_switches = KillSwitchInputs(
        nullity_confirmed=kill_data.get("nullity_confirmed", False),
        regulatory_open=kill_data.get("regulatory_open", False),
        insurer_notice=kill_data.get("insurer_notice", False),
        override_admitted=kill_data.get("override_admitted", False),
        shadow_director=kill_data.get("shadow_director", False),
    )
    
    # Containment inputs
    containment_data = inputs.get("containment", {})
    containment = ContainmentInputs(
        containment_exposure_gbp=containment_data.get("containment_exposure_gbp", 0.0),
        reputational_damage_gbp=containment_data.get("reputational_damage_gbp", 0.0),
        regulatory_fine_risk_gbp=containment_data.get("regulatory_fine_risk_gbp", 0.0),
        litigation_cascade_risk_gbp=containment_data.get("litigation_cascade_risk_gbp", 0.0),
    )
    
    # Stance
    stance_data = inputs.get("stance", {})
    stance = NegotiationStance(
        anchor_gbp=stance_data.get("anchor_gbp", 15_000_000.0),
        minimum_objective_gbp=stance_data.get("minimum_objective_gbp", 9_000_000.0),
        objective_mode=stance_data.get("objective_mode", "standard"),
    )
    
    # Fear override
    fear_override = inputs.get("fear_override")
    
    return {
        "procedural": procedural,
        "monetary": monetary,
        "kill_switches": kill_switches,
        "containment": containment,
        "stance": stance,
        "fear_override": fear_override,
    }


def render_import_panel() -> dict | None:
    """Render the Import JSON panel.
    
    Returns:
        Dict of extracted inputs if import successful, None otherwise.
    """
    st.subheader("📥 Import Run from JSON")
    
    with st.expander("What this panel does"):
        st.markdown("""
        **Purpose**: Load a previously saved run or RAG-generated JSON to populate the dashboard.
        
        **Supported Formats**:
        1. **full_run*.json** — Exported from dashboard (complete data)
        2. **Calibration Output** — From NotebookLM/LLM analysis (extracts SVs and inferred kill switches)
        
        **How to use**:
        1. Upload a JSON file or paste JSON text directly
        2. Click "Import and Apply" to populate dashboard controls
        """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload JSON file",
        type=["json"],
        help="full_run*.json or calibration output",
    )
    
    # Text paste area
    json_text = st.text_area(
        "Or paste JSON text directly",
        placeholder='{"inputs": {...}} or {"engine_snapshot": {...}}',
        height=150,
    )
    
    # Load from uploaded file or text
    data: dict[str, Any] | None = None
    source = None
    
    if uploaded_file is not None:
        try:
            data = json.loads(uploaded_file.read().decode("utf-8"))
            source = f"file: {uploaded_file.name}"
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in uploaded file: {e}")
            return None
    
    if json_text.strip():
        try:
            data = json.loads(json_text)
            source = "pasted text"
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON in pasted text: {e}")
            return None
    
    if data is not None:
        # Validate and detect format
        is_valid, message, json_format = validate_imported_json(data)
        
        if not is_valid:
            st.error(f"Validation failed: {message}")
            return None
        
        # Show preview based on format
        with st.expander("Preview imported data"):
            st.write(f"**Format detected**: {json_format}")
            
            if json_format == "full_run":
                inputs = data.get("inputs", {})
                proc = inputs.get("procedural", {})
                st.write(f"**SV1a/SV1b/SV1c**: {proc.get('SV1a')}/{proc.get('SV1b')}/{proc.get('SV1c')}")
                st.write(f"**Mode**: {inputs.get('stance', {}).get('objective_mode', 'standard')}")
                st.write(f"**Fear Override**: {inputs.get('fear_override', 'None')}")
                
                # Show active kill switches
                kill = inputs.get("kill_switches", {})
                active = [k for k, v in kill.items() if v]
                if active:
                    st.write(f"**Active Events**: {', '.join(active)}")
                else:
                    st.write("**Active Events**: None")
            
            elif json_format == "calibration_output":
                engine_snapshot = data.get("engine_snapshot", {})
                inputs = engine_snapshot.get("inputs", {})
                st.write(f"**SV1a/SV1b/SV1c**: {inputs.get('SV1a')}/{inputs.get('SV1b')}/{inputs.get('SV1c')}")
                
                # Show inferred kill switches
                kill = _infer_kill_switches_from_calibration(data)
                active = [k for k, v in kill.model_dump().items() if v]
                if active:
                    st.write(f"**Inferred Active Events**: {', '.join(active)}")
                else:
                    st.write("**Inferred Active Events**: None")
                
                st.caption("Note: Calibration output format provides limited data. Full monetary/containment values use defaults.")
        
        # Import button
        if st.button("Import and Apply", type="primary"):
            extracted = extract_inputs_from_json(data, json_format)
            st.success(f"✅ Imported from {source} ({json_format} format)")
            st.info("Dashboard controls have been populated. Review and adjust as needed.")
            return extracted
    
    return None
