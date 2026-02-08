"""Import JSON panel for loading saved runs into the dashboard."""

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


def validate_imported_json(data: dict) -> tuple[bool, str]:
    """Validate that imported JSON has required structure.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_keys = ["inputs"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: {key}"
    
    inputs = data.get("inputs", {})
    
    # Check for procedural inputs
    if "procedural" not in inputs:
        return False, "Missing inputs.procedural"
    
    proc = inputs["procedural"]
    if not all(k in proc for k in ["SV1a", "SV1b", "SV1c"]):
        return False, "Missing SV1a/SV1b/SV1c in procedural inputs"
    
    return True, "Valid"


def extract_inputs_from_json(data: dict) -> dict:
    """Extract input values from imported JSON.
    
    Returns dict with keys: procedural, monetary, kill_switches, 
    containment, stance, fear_override
    """
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
        
        **How to use**:
        1. Upload a `full_run*.json` file from a previous session, OR
        2. Paste JSON text directly from RAG output
        3. Click "Import and Apply" to populate all dashboard controls
        
        **Validation**: The JSON must contain `inputs.procedural` with SV1a/SV1b/SV1c values.
        """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload JSON file (full_run*.json)",
        type=["json"],
        help="Select a previously exported JSON file",
    )
    
    # Text paste area
    json_text = st.text_area(
        "Or paste JSON text directly",
        placeholder='{"inputs": {"procedural": {"SV1a": 0.5, ...}, ...}, ...}',
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
        # Validate
        is_valid, message = validate_imported_json(data)
        
        if not is_valid:
            st.error(f"Validation failed: {message}")
            return None
        
        # Show preview
        with st.expander("Preview imported data"):
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
        
        # Import button
        if st.button("Import and Apply", type="primary"):
            extracted = extract_inputs_from_json(data)
            st.success(f"✅ Imported from {source}")
            st.info("Dashboard controls have been populated. Review and adjust as needed.")
            return extracted
    
    return None
