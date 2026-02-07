"""
Simple web UI for Procedural Leverage Engine.

This provides a live calculator for settlement discussions that's more
persuasive than showing JSON to clients or during negotiations.

Usage:
    pip install streamlit
    streamlit run web_ui.py

Then open http://localhost:8501 in your browser.
"""

import sys
from pathlib import Path
import streamlit as st

# Add parent directory to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from probabilistic.adapters import run_deterministic_engine


def main():
    """Main Streamlit application."""
    
    # Page config
    st.set_page_config(
        page_title="Procedural Leverage Engine",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ Procedural Leverage Engine")
    st.markdown("""
    **Commercial Dispute Settlement Decision Support**
    
    This tool calculates Unified Procedural Leverage Score (UPLS) and provides
    posture recommendations for commercial litigation negotiations.
    """)
    
    st.sidebar.header("Inputs")
    
    # Input sliders
    st.sidebar.subheader("Success Vector Parameters")
    
    sv1a = st.sidebar.slider(
        "SV1a (Claim Validity)",
        min_value=0.0,
        max_value=1.0,
        value=0.38,
        step=0.01,
        help="Claim validity strength: How strong is your legal authority?"
    )
    
    sv1b = st.sidebar.slider(
        "SV1b (Procedural Advantage)",
        min_value=0.0,
        max_value=1.0,
        value=0.86,
        step=0.01,
        help="Procedural advantage: Can you hurt them procedurally?"
    )
    
    sv1c = st.sidebar.slider(
        "SV1c (Cost Asymmetry)",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.01,
        help="Cost asymmetry: Who bleeds faster if this drags on?"
    )
    
    st.sidebar.markdown("---")
    
    # Calculate button
    if st.sidebar.button("Calculate", type="primary"):
        # Run engine
        result = run_deterministic_engine(
            state={"SV1a": sv1a, "SV1b": sv1b, "SV1c": sv1c}
        )
        
        # Display results
        st.header("Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("UPLS", value="{:.3f}".format(result.scores.upls))
            st.caption("Unified Procedural Leverage Score")
        
        with col2:
            st.metric("Decision", value=result.evaluation.decision)
            st.caption("Recommended posture")
        
        with col3:
            st.metric("Tripwire", value="{:.2f}".format(result.scores.tripwire))
            st.caption("Leverage threshold")
        
        with col4:
            st.metric("Confidence", value=result.evaluation.confidence)
            st.caption("Assessment certainty")
        
        # Tripwire warning
        if result.evaluation.tripwire_triggered:
            st.warning("⚠️ TRIPWIRE TRIGGERED - Leverage threshold exceeded")
        else:
            st.success("✓ Tripwire clear - Posture sustainable")
        
        # Interpretation
        st.header("Interpretation")
        
        # Leverage position
        st.subheader("Leverage Position")
        st.info(result.interpretation.leverage_position)
        
        # Decision explanation
        st.subheader("Decision Explanation")
        st.write(result.interpretation.decision_explanation)
        
        # Tripwire status
        st.subheader("Tripwire Status")
        st.write(result.interpretation.tripwire_status)
        
        # Confidence explanation
        st.subheader("Confidence")
        st.write(result.interpretation.confidence_explanation)
        
        # Inputs summary
        with st.expander("View Input Parameters"):
            st.json({
                "SV1a (Claim Validity)": sv1a,
                "SV1b (Procedural Advantage)": sv1b,
                "SV1c (Cost Asymmetry)": sv1c
            })
        
        # Full output
        with st.expander("View Full JSON Output"):
            st.json({
                "inputs": result.inputs,
                "scores": {
                    "upls": result.scores.upls,
                    "tripwire": result.scores.tripwire
                },
                "evaluation": {
                    "decision": result.evaluation.decision,
                    "confidence": result.evaluation.confidence,
                    "tripwire_triggered": result.evaluation.tripwire_triggered
                },
                "interpretation": result.interpretation.__dict__
            })
    
    else:
        st.info("👆 Click 'Calculate' to analyze your position")


if __name__ == "__main__":
    main()