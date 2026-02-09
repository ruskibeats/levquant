"""Production-style analytical dashboard for procedural leverage decision support."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure local imports resolve when run via `streamlit run web/dashboard.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_assistant.context_journal import add_context, get_all_context, read_entries
from ai_assistant.daily_calibration import (
    DailyAICalibrator,
    export_prompt_markdown,
    save_daily_report,
)
from ai_assistant.prompt_loader import get_prompt_metadata
from cli.run import run_engine
from decision_support.monetary import ASSUMPTIONS, build_audit_bundle, build_pdf_summary, build_pricing, detect_low_range_causes
from decision_support.schemas import ContainmentInputs, NegotiationStance
from decision_support.questionnaire import (
    default_kill_switch_inputs,
    default_monetary_inputs,
    default_procedural_inputs,
)
from decision_support.scenario_pricer import (
    build_heatmap_dataframe,
    build_scenario_table,
    export_scenario_matrix,
    run_validation_battery,
)
from decision_support.schemas import KillSwitchInputs, MonetaryInputs, ProceduralInputs
from web.components.assumptions_panel import render_assumptions_panel
from web.components.contagion_map import render_contagion_panel
from web.components.corridor_panel import render_corridor_panel
from web.components.heatmap_panel import render_heatmap_panel
from web.components.import_panel import render_import_panel
from web.components.kpi_panel import render_kpi_panel
from web.components.scenario_table import render_scenario_table
from web.components.validation_panel import render_validation_panel


def _to_dict(value):
    return value.model_dump() if hasattr(value, "model_dump") else value


def _position_strength_text(upls: float) -> str:
    if upls >= 0.8:
        return "very strong"
    if upls >= 0.6:
        return "strong"
    if upls >= 0.4:
        return "balanced"
    return "fragile"


def _pressure_impact_text(tripwire: float) -> str:
    return "hurts them more than us" if tripwire >= 7.5 else "is still building and needs monitoring"


def _get_session_value(key: str, default_value):
    """Get value from session state or use default."""
    return st.session_state.get(key, default_value)


def _render_import_section():
    """Render the import panel section."""
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
    
    # Use the import panel component
    imported = render_import_panel()
    
    if imported:
        # Store imported values in session state
        st.session_state.imported_sv1a = imported["procedural"].SV1a
        st.session_state.imported_sv1b = imported["procedural"].SV1b
        st.session_state.imported_sv1c = imported["procedural"].SV1c
        st.session_state.imported_principal = imported["monetary"].principal_debt_gbp
        st.session_state.imported_claimant_costs = imported["monetary"].claimant_costs_gbp
        st.session_state.imported_defendant_costs = imported["monetary"].defendant_costs_estimate_gbp
        st.session_state.imported_regulatory = imported["monetary"].regulatory_exposure_gbp
        st.session_state.imported_transaction = imported["monetary"].transaction_value_gbp
        st.session_state.imported_nullity = imported["kill_switches"].nullity_confirmed
        st.session_state.imported_regulatory_open = imported["kill_switches"].regulatory_open
        st.session_state.imported_insurer = imported["kill_switches"].insurer_notice
        st.session_state.imported_override = imported["kill_switches"].override_admitted
        st.session_state.imported_shadow = imported["kill_switches"].shadow_director
        st.session_state.imported_fear = imported["fear_override"]
        st.session_state.imported_containment = imported["containment"].containment_exposure_gbp
        st.session_state.imported_reputational = imported["containment"].reputational_damage_gbp
        st.session_state.imported_fine = imported["containment"].regulatory_fine_risk_gbp
        st.session_state.imported_cascade = imported["containment"].litigation_cascade_risk_gbp
        st.session_state.imported_anchor = imported["stance"].anchor_gbp
        st.session_state.imported_minimum = imported["stance"].minimum_objective_gbp
        st.session_state.imported_mode = imported["stance"].objective_mode
        st.session_state.imported_notes = imported["monetary"].assumptions_notes
        st.success("✅ Import successful! Values applied to sidebar controls.")
        st.info("The imported values are now active. Review and adjust as needed.")
        return True
    return False


def _render_daily_ai_panel(
    proc: ProceduralInputs,
    money: MonetaryInputs,
    kill: KillSwitchInputs,
    fear_override: float | None,
    priced: dict,
) -> None:
    """Render the Daily AI (Calibration) panel."""
    st.subheader("Daily AI (Calibration)")

    # Show locked prompt badge
    prompt_meta = get_prompt_metadata("v1")
    st.info(
        f"🔒 **Calibration Prompt**: `{prompt_meta['template_tag']}` (locked) | "
        f"{prompt_meta['size_chars']:,} chars | "
        f"{prompt_meta['line_count']} lines"
    )
    st.caption(
        "This prompt is loaded verbatim from a source-of-truth file. "
        "It cannot be edited to ensure methodology consistency and legal defensibility."
    )

    with st.expander("What this panel does"):
        st.markdown("""
        **Purpose**: Capture new context, store it in a journal, and generate a NotebookLM-ready
        calibration prompt for your RAG LLM.

        **How to use**:
        1. Paste any new information (emails, court notes, timeline updates) into the text area
        2. Select the entry type
        3. Click "Save to Journal" to append it with a timestamp
        4. Click "Generate NotebookLM Prompt" to create a calibration audit prompt
        5. Copy the prompt and paste it into NotebookLM for analysis

        **No external APIs are called** — this is purely for prompt generation.
        """)

    # Get current journal stats
    entries = read_entries()
    entries_count = len(entries)
    last_entry_ts = entries[-1]["timestamp_utc"] if entries else "None"

    col1, col2, col3 = st.columns(3)
    col1.metric("Journal Entries", entries_count)
    col2.metric("Last Entry", last_entry_ts[:19] if entries else "None")

    # New context input
    new_context = st.text_area(
        "New context (paste anything new today)",
        placeholder="Examples:\n• New email from opposing counsel\n• HMCTS notification\n• Timeline update\n• Document metadata discovery",
        height=150,
    )

    entry_type = st.selectbox(
        "Entry type",
        options=["text", "email", "court_note", "phone_call", "other"],
        index=0,
    )

    include_full_journal = st.checkbox("Include full journal in prompt", value=True)
    entry_limit = st.slider(
        "Limit entries (0 = all)",
        min_value=0,
        max_value=min(100, max(10, entries_count)),
        value=0,
        disabled=not include_full_journal,
    )

    # Buttons row
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Save to Journal", disabled=not new_context.strip()):
            try:
                add_context(
                    doc_text=new_context,
                    entry_type=entry_type,
                    source="dashboard",
                )
                st.success("Context saved to journal!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # Store generated prompt in session state
    if "generated_prompt" not in st.session_state:
        st.session_state.generated_prompt = None
    if "saved_report_path" not in st.session_state:
        st.session_state.saved_report_path = None

    with c2:
        if st.button("Generate NotebookLM Prompt"):
            with st.spinner("Building calibration prompt..."):
                # Get context
                limit = entry_limit if entry_limit > 0 else None
                all_context = get_all_context(limit=limit) if include_full_journal else ""

                # Get engine snapshot using run_engine directly
                engine_result = run_engine(state={"SV1a": proc.SV1a, "SV1b": proc.SV1b, "SV1c": proc.SV1c})

                # Build calibrator and generate prompt
                calibrator = DailyAICalibrator(llm_client=None)  # No LLM, just prompt generation

                # Prepare assumptions snapshot
                assumptions_snapshot = {
                    **ASSUMPTIONS,
                    "current_posture": priced.get("posture", "NORMAL"),
                    "fear_index": priced.get("fear_index", 0.0),
                    "kill_switches_active": priced.get("kill_switches_active", []),
                }

                result = calibrator.run(
                    new_context=new_context,
                    all_context=all_context,
                    engine_snapshot=engine_result,
                    assumptions_snapshot=assumptions_snapshot,
                )

                st.session_state.generated_prompt = result["raw_prompt"]
                st.session_state.last_result = result

    with c3:
        if st.button("Export Daily Report JSON"):
            if st.session_state.get("last_result"):
                report_path = save_daily_report(
                    st.session_state.last_result,
                    outputs_dir=PROJECT_ROOT / "outputs",
                )
                st.session_state.saved_report_path = str(report_path)
                st.success(f"Saved to: {report_path.name}")
            else:
                st.warning("Generate prompt first")

    # Show latest entries
    if entries:
        with st.expander(f"Show journal (latest {min(10, entries_count)} entries)"):
            for entry in entries[-10:]:
                st.markdown(
                    f"**[{entry['timestamp_utc'][:19]}]** *{entry['entry_type']}*  \n"
                    f"{entry['text'][:200]}{'...' if len(entry['text']) > 200 else ''}"
                )

    # Display generated prompt
    if st.session_state.generated_prompt:
        st.markdown("---")
        st.markdown("### Generated NotebookLM Prompt")
        st.caption("Copy this prompt and paste it into NotebookLM for analysis")

        st.code(st.session_state.generated_prompt, language="markdown")

        # Copy and export buttons
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Copy to Clipboard (simulated)"):
                st.success("Prompt ready in code block above — select all and copy")
        with col_b:
            if st.button("Export Prompt as Markdown"):
                md_path = export_prompt_markdown(
                    st.session_state.generated_prompt,
                    outputs_dir=PROJECT_ROOT / "outputs",
                )
                st.success(f"Saved: {md_path.name}")


def main() -> None:
    st.set_page_config(page_title="LEVQUANT Decision Support", page_icon="⚖️", layout="wide")
    st.title("LEVQUANT Decision Support Dashboard")
    st.caption("Deterministic, auditable, reproducible | engine truth + explicit pricing assumptions")

    with st.expander("Need plain English? Click here"):
        st.markdown(
            """
            **Quick translation guide**

            - **Position Strength (UPLS)** = overall strength of your legal position
            - **Pressure Level (Tripwire)** = urgency to act (0–10)
            - **Recommended Action (Decision)** = what to do right now
            - **Settlement Range** = minimum / likely / aim / maximum offer
            - **Events That Change Everything (Kill-switches)** = rare events that can rapidly change posture
            """
        )

    # Get defaults
    proc0 = default_procedural_inputs()
    money0 = default_monetary_inputs()
    kill0 = default_kill_switch_inputs()

    # Import panel in main content area (at the top, before sidebar inputs)
    st.markdown("---")
    _render_import_section()
    st.markdown("---")

    st.sidebar.header("Input Control Panel")
    
    # Settlement Objective Mode
    st.sidebar.subheader("Settlement Objective Mode")
    
    # Use imported mode if available, otherwise default
    default_mode = _get_session_value("imported_mode", "standard")
    objective_mode = st.sidebar.radio(
        "Select pricing mode:",
        options=["standard", "containment", "anchor_driven"],
        index=["standard", "containment", "anchor_driven"].index(default_mode),
        format_func=lambda x: {
            "standard": "Standard dispute pricing",
            "containment": "Containment pricing (misconduct/regulatory risk)",
            "anchor_driven": "Anchor-driven negotiation (15m/9m guardrails)",
        }[x],
        help="Changes how the GBP corridor is calculated.",
    )
    
    # Negotiation Stance inputs
    if objective_mode in ("containment", "anchor_driven"):
        with st.sidebar.expander("Negotiation Stance (Anchor/Minimum)"):
            anchor_gbp = st.number_input(
                "Opening demand / Anchor (£)",
                min_value=0.0,
                value=_get_session_value("imported_anchor", 15_000_000.0),
                step=1_000_000.0,
                help="Your opening negotiation position. Default £15m.",
            )
            minimum_objective_gbp = st.number_input(
                "Walk-away minimum (£)",
                min_value=0.0,
                value=_get_session_value("imported_minimum", 9_000_000.0),
                step=1_000_000.0,
                help="Your minimum acceptable settlement. Default £9m.",
            )
    else:
        anchor_gbp = _get_session_value("imported_anchor", 15_000_000.0)
        minimum_objective_gbp = _get_session_value("imported_minimum", 9_000_000.0)
    
    simple_mode = st.sidebar.checkbox("Plain English Mode", value=True)
    
    # Procedural inputs with imported values as defaults
    sv1a = st.sidebar.slider(
        "Right to Bring the Claim (SV1a)",
        0.0,
        1.0,
        _get_session_value("imported_sv1a", float(proc0.SV1a)),
        0.01,
        help="Do you legally have the right/authority to make this claim?",
    )
    sv1b = st.sidebar.slider(
        "Rule-Breaking Leverage (SV1b)",
        0.0,
        1.0,
        _get_session_value("imported_sv1b", float(proc0.SV1b)),
        0.01,
        help="How much pressure can be applied based on their rule-breaking?",
    )
    sv1c = st.sidebar.slider(
        "Cost Pressure on Them (SV1c)",
        0.0,
        1.0,
        _get_session_value("imported_sv1c", float(proc0.SV1c)),
        0.01,
        help="Are your costs much lower than theirs?",
    )

    st.sidebar.subheader("Monetary Inputs")
    principal = st.sidebar.number_input(
        "Principal debt (£)", 
        min_value=0.0, 
        value=_get_session_value("imported_principal", float(money0.principal_debt_gbp)), 
        step=10000.0
    )
    claimant_costs = st.sidebar.number_input(
        "Claimant costs (£)", 
        min_value=0.0, 
        value=_get_session_value("imported_claimant_costs", float(money0.claimant_costs_gbp)), 
        step=10000.0
    )
    defendant_costs = st.sidebar.number_input(
        "Defendant costs estimate (£)", 
        min_value=0.0, 
        value=_get_session_value("imported_defendant_costs", float(money0.defendant_costs_estimate_gbp)), 
        step=10000.0
    )
    regulatory_exposure = st.sidebar.number_input(
        "Regulatory exposure (£)", 
        min_value=0.0, 
        value=_get_session_value("imported_regulatory", float(money0.regulatory_exposure_gbp)), 
        step=10000.0
    )
    transaction_value = st.sidebar.number_input(
        "Transaction value (£, optional)", 
        min_value=0.0, 
        value=_get_session_value("imported_transaction", float(money0.transaction_value_gbp)), 
        step=10000.0
    )
    
    # Containment Inputs
    if objective_mode in ("containment", "anchor_driven"):
        st.sidebar.subheader("Containment Exposure (Misconduct Risk)")
        containment_exposure = st.sidebar.number_input(
            "Total containment exposure if public (£)",
            min_value=0.0,
            value=_get_session_value("imported_containment", 0.0),
            step=1_000_000.0,
            help="Total cost if misconduct becomes public",
        )
        reputational_damage = st.sidebar.number_input(
            "Reputational/fiduciary damage (£)",
            min_value=0.0,
            value=_get_session_value("imported_reputational", 0.0),
            step=500_000.0,
            help="Estimated reputational harm",
        )
        regulatory_fine_risk = st.sidebar.number_input(
            "Regulatory fine risk (£)",
            min_value=0.0,
            value=_get_session_value("imported_fine", 0.0),
            step=500_000.0,
            help="SRA, FCA, or other regulatory fines",
        )
        litigation_cascade_risk = st.sidebar.number_input(
            "Follow-on litigation risk (£)",
            min_value=0.0,
            value=_get_session_value("imported_cascade", 0.0),
            step=500_000.0,
            help="Risk of claims from other parties",
        )
    else:
        containment_exposure = _get_session_value("imported_containment", 0.0)
        reputational_damage = _get_session_value("imported_reputational", 0.0)
        regulatory_fine_risk = _get_session_value("imported_fine", 0.0)
        litigation_cascade_risk = _get_session_value("imported_cascade", 0.0)
    
    notes = st.sidebar.text_area(
        "Notes on assumptions", 
        value=_get_session_value("imported_notes", money0.assumptions_notes)
    )

    st.sidebar.subheader("Events That Change Everything")
    nullity = st.sidebar.checkbox(
        "Claim validity collapses (nullity confirmed)",
        value=_get_session_value("imported_nullity", kill0.nullity_confirmed),
        help="Technical key: nullity_confirmed",
    )
    regulatory_open = st.sidebar.checkbox(
        "Regulatory investigation is open",
        value=_get_session_value("imported_regulatory_open", kill0.regulatory_open),
        help="Technical key: regulatory_open",
    )
    insurer_notice = st.sidebar.checkbox(
        "Insurer has been notified",
        value=_get_session_value("imported_insurer", kill0.insurer_notice),
        help="Technical key: insurer_notice",
    )
    override_admitted = st.sidebar.checkbox(
        "Administrative override admitted",
        value=_get_session_value("imported_override", kill0.override_admitted),
        help="Technical key: override_admitted",
    )
    shadow_director = st.sidebar.checkbox(
        "Shadow director evidence established",
        value=_get_session_value("imported_shadow", kill0.shadow_director),
        help="Technical key: shadow_director",
    )

    st.sidebar.subheader("Weakest-Link Stress Level Override")
    imported_fear = st.session_state.get("imported_fear")
    use_fear_override = st.sidebar.checkbox(
        "Enable stress override", 
        value=imported_fear is not None
    )
    fear_override = (
        st.sidebar.slider(
            "Weakest-Link Stress Level",
            0.0,
            1.0,
            imported_fear if imported_fear is not None else 0.0,
            0.01,
            help="0.0 = no stress, 1.0 = extreme stress",
        )
        if use_fear_override
        else None
    )

    proc = ProceduralInputs(SV1a=sv1a, SV1b=sv1b, SV1c=sv1c)
    money = MonetaryInputs(
        principal_debt_gbp=principal,
        claimant_costs_gbp=claimant_costs,
        defendant_costs_estimate_gbp=defendant_costs,
        regulatory_exposure_gbp=regulatory_exposure,
        transaction_value_gbp=transaction_value,
        assumptions_notes=notes,
    )
    kill = KillSwitchInputs(
        nullity_confirmed=nullity,
        regulatory_open=regulatory_open,
        insurer_notice=insurer_notice,
        override_admitted=override_admitted,
        shadow_director=shadow_director,
    )
    containment = ContainmentInputs(
        containment_exposure_gbp=containment_exposure,
        reputational_damage_gbp=reputational_damage,
        regulatory_fine_risk_gbp=regulatory_fine_risk,
        litigation_cascade_risk_gbp=litigation_cascade_risk,
    )
    stance = NegotiationStance(
        anchor_gbp=anchor_gbp,
        minimum_objective_gbp=minimum_objective_gbp,
        objective_mode=objective_mode,
    )

    priced = build_pricing(
        proc=proc,
        money=money,
        kill_switches=kill,
        fear_override=fear_override,
        containment=containment,
        stance=stance,
    )

    st.subheader("What this means right now")
    
    # Event escalation feedback
    active_events = priced.get("kill_switches_active", [])
    event_count = len(active_events)
    
    if event_count > 0:
        st.warning(
            f"⚡ **{event_count} Event{'s' if event_count > 1 else ''} That Changes Everything active** — "
            f"Range adjusted due to existential risk factors"
        )
    
    # Dual Range Display
    dual = priced.get("dual_corridor")
    if dual:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Model Range (Input-Driven)", f"£{dual.model_floor_gbp:,.0f} – £{dual.model_ceiling_gbp:,.0f}")
            st.caption(f"Target: £{dual.model_target_gbp:,.0f}")
        with col2:
            st.metric("Negotiation Range (Stance)", f"£{dual.negotiation_minimum_gbp:,.0f} – £{dual.negotiation_anchor_gbp:,.0f}")
            st.caption(f"Anchor: £{dual.negotiation_anchor_gbp:,.0f} | Minimum: £{dual.negotiation_minimum_gbp:,.0f}")
        
        if dual.range_alignment == "below_objective":
            st.warning(f"⚠️ {dual.explanation}")
        elif dual.range_alignment == "aligned":
            st.success(f"✓ {dual.explanation}")
    
    st.success(
        f"• Our overall position is **{_position_strength_text(priced['engine'].upls)}**.\n"
        f"• Pressure level is **{priced['engine'].tripwire:.1f}/10**.\n"
        f"• The system recommends **{priced['posture']}** behaviour."
    )

    # Rest of dashboard...
    render_kpi_panel(priced)
    render_corridor_panel(priced)
    
    st.markdown("---")
    render_contagion_panel(kill.model_dump())

    st.subheader("How the settlement figure is built")
    breakdown_df = pd.DataFrame([b.model_dump() for b in priced["breakdown"]])
    st.dataframe(breakdown_df)
    
    stack_fig = px.bar(
        breakdown_df,
        x="component",
        y="amount_gbp",
        hover_data=["formula", "source", "assumption"],
        title="Settlement Building Blocks",
    )
    st.plotly_chart(stack_fig)

    heatmap_df = build_heatmap_dataframe(money=money, kill=kill, fixed_sv1c=sv1c, fear_override=fear_override)
    render_heatmap_panel(heatmap_df)

    scenario_rows = build_scenario_table(money=money, kill=kill, fear_override=fear_override)
    scenario_dicts = [s.model_dump() for s in scenario_rows]
    render_scenario_table(scenario_dicts)

    # Export
    report_payload = {
        "inputs": {
            "procedural": proc.model_dump(),
            "monetary": money.model_dump(),
            "kill_switches": kill.model_dump(),
            "fear_override": fear_override,
            "containment": containment.model_dump(),
            "stance": stance.model_dump(),
        },
        "engine": _to_dict(priced["engine"]),
        "corridor": _to_dict(priced["corridor"]),
        "dual_corridor": _to_dict(priced.get("dual_corridor")),
        "breakdown": [_to_dict(b) for b in priced["breakdown"]],
        "posture": priced["posture"],
        "fear_index": priced["fear_index"],
        "kill_switches_active": priced["kill_switches_active"],
    }
    audit_bundle = build_audit_bundle(report_payload)
    
    st.subheader("Export and Evidence")
    export_json = json.dumps({**report_payload, "audit": audit_bundle.model_dump(mode="json")}, indent=2)
    st.download_button("Download Evidence Pack (JSON)", data=export_json.encode("utf-8"), file_name="full_run.json", mime="application/json")

    pdf_bytes = build_pdf_summary(report_payload)
    st.download_button("Download Court-Ready Summary (PDF)", data=pdf_bytes, file_name="court_safe_summary.pdf", mime="application/pdf")

    # Daily AI Panel
    st.markdown("---")
    _render_daily_ai_panel(proc, money, kill, fear_override, priced)


if __name__ == "__main__":
    main()
