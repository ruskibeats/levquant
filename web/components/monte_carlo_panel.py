"""Monte Carlo simulation panel for probabilistic risk analysis."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np

from probabilistic.monte_carlo import NormalDistribution, monte_carlo_sample


def render_monte_carlo_panel(sv1a: float, sv1b: float, sv1c: float) -> None:
    st.subheader("Probabilistic Risk Analysis (Monte Carlo)")
    
    with st.expander("About Monte Carlo Simulation", expanded=False):
        st.markdown("""
        **Purpose**: Assess how uncertainty in your inputs (SV1a, SV1b, SV1c) impacts the final decision.
        
        **How it works**:
        1. We treat your current inputs as the 'Mean' (expected value).
        2. We assume a level of uncertainty (Standard Deviation).
        3. We run thousands of simulated scenarios to see the distribution of outcomes.
        
        **New Features**:
        - **Reproducible Seed**: Set a seed for identical results across runs
        - **Convergence Tracking**: Verify simulation stability
        - **Histogram Visualization**: See full distribution shapes
        - **Worst-Case Identification**: Find scenarios with extreme outcomes
        """)

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Simulation Parameters")
        n_samples = st.select_slider(
            "Samples",
            options=[1000, 5000, 10000, 50000],
            value=10000,
            help="Higher samples = higher precision but slower execution."
        )
        
        uncertainty = st.slider(
            "Input Uncertainty (std dev)",
            0.01, 0.20, 0.05, 0.01,
            help="How much variation to allow around your current inputs."
        )
        
        # Seed input for reproducibility
        use_seed = st.checkbox("Set Random Seed (for reproducibility)", value=False)
        seed = None
        if use_seed:
            seed = st.number_input(
                "Seed Value (0-9999)",
                min_value=0,
                max_value=9999,
                value=42,
                step=1,
                help="Use the same seed to get identical results."
            )
        
        if st.button("Run Simulation", type="primary"):
            with st.spinner(f"Running {n_samples:,} simulations..."):
                # Define distributions
                sv1a_dist = NormalDistribution(mean=sv1a, std=uncertainty)
                sv1b_dist = NormalDistribution(mean=sv1b, std=uncertainty)
                sv1c_dist = NormalDistribution(mean=sv1c, std=uncertainty)
                
                # Run simulation with seed and convergence tracking
                result = monte_carlo_sample(
                    n_samples=n_samples,
                    sv1a_dist=sv1a_dist,
                    sv1b_dist=sv1b_dist,
                    sv1c_dist=sv1c_dist,
                    seed=seed,
                    track_convergence=True
                )
                
                # Store in session state
                st.session_state.mc_result = result
                st.success("Simulation complete!")

    if "mc_result" in st.session_state:
        result = st.session_state.mc_result
        
        with col2:
            st.markdown("### Decision Probability Distribution")
            
            # Decision proportions chart
            decisions = list(result.decision_proportions.keys())
            proportions = list(result.decision_proportions.values())
            
            fig = px.pie(
                values=proportions,
                names=decisions,
                color=decisions,
                color_discrete_map={
                    "ACCEPT": "#4CAF50",
                    "COUNTER": "#FFC107",
                    "HOLD": "#2196F3",
                    "REJECT": "#F44336"
                },
                hole=0.4,
                title="Likelihood of Recommended Actions"
            )
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        
        # Display seed if used
        if result.meta.get('seed') is not None:
            st.info(f"🔢 **Random Seed Used**: {result.meta['seed']} (reproducible)")
        
        # UPLS Distribution
        st.markdown("### UPLS Confidence Intervals")
        upls = result.upls_distribution
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean UPLS", f"{upls['mean']:.3f}")
        c2.metric("Median", f"{upls['median']:.3f}")
        c3.metric("5th Percentile", f"{upls['percentile_5']:.3f}")
        c4.metric("95th Percentile", f"{upls['percentile_95']:.3f}")
        
        # Range visualization
        st.caption(f"We are 90% confident the UPLS lies between {upls['percentile_5']:.3f} and {upls['percentile_95']:.3f}")
        
        # UPLS Histogram
        if 'samples' in upls:
            st.markdown("#### UPLS Distribution Histogram")
            fig_upls = px.histogram(
                x=upls['samples'],
                nbins=50,
                title="UPLS Distribution",
                labels={'x': 'UPLS Value', 'count': 'Frequency'},
                color_discrete_sequence=['#c5a059']
            )
            # Add vertical lines for mean and percentiles
            fig_upls.add_vline(x=upls['mean'], line_dash="dash", line_color="white", annotation_text="Mean")
            fig_upls.add_vline(x=upls['percentile_5'], line_dash="dot", line_color="red", annotation_text="5th %ile")
            fig_upls.add_vline(x=upls['percentile_95'], line_dash="dot", line_color="red", annotation_text="95th %ile")
            fig_upls.update_layout(height=300)
            st.plotly_chart(fig_upls, use_container_width=True)
        
        # Simple probability bar
        st.markdown(f"""
        <div style="width: 100%; background-color: #333; height: 10px; border-radius: 5px; margin-top: 20px; position: relative;">
            <div style="position: absolute; left: {upls['percentile_5']*100}%; width: {(upls['percentile_95'] - upls['percentile_5'])*100}%; background-color: #c5a059; height: 10px; border-radius: 5px; opacity: 0.5;"></div>
            <div style="position: absolute; left: {upls['mean']*100}%; width: 4px; background-color: #fff; height: 16px; top: -3px; border-radius: 2px;" title="Mean"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #888; margin-top: 5px;">
            <span>0.0</span>
            <span>0.5</span>
            <span>1.0</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Tripwire Distribution
        st.markdown("### Tripwire Distribution")
        tripwire = result.tripwire_distribution
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean Tripwire", f"{tripwire['mean']:.2f}")
        c2.metric("Median", f"{tripwire['median']:.2f}")
        c3.metric("Min", f"{tripwire['min']:.2f}")
        c4.metric("Max", f"{tripwire['max']:.2f}")
        
        # Tripwire Histogram
        if 'samples' in tripwire:
            st.markdown("#### Tripwire Distribution Histogram")
            fig_trip = px.histogram(
                x=tripwire['samples'],
                nbins=50,
                title="Tripwire Distribution",
                labels={'x': 'Tripwire Value', 'count': 'Frequency'},
                color_discrete_sequence=['#2196F3']
            )
            # Add vertical lines for mean and threshold
            fig_trip.add_vline(x=tripwire['mean'], line_dash="dash", line_color="white", annotation_text="Mean")
            fig_trip.add_vline(x=7.5, line_dash="solid", line_color="red", annotation_text="Alert Threshold")
            fig_trip.update_layout(height=300)
            st.plotly_chart(fig_trip, use_container_width=True)
        
        st.markdown("---")
        
        # Convergence Diagnostics
        if result.meta.get('convergence'):
            st.markdown("### Convergence Diagnostics")
            conv = result.meta['convergence']
            
            col_conv1, col_conv2, col_conv3 = st.columns(3)
            
            with col_conv1:
                if conv['converged']:
                    st.success("✅ Converged")
                else:
                    st.warning("⚠️ Not Converged")
            
            with col_conv2:
                st.metric("SEM (UPLS)", f"{conv['sem_upls']:.4f}")
            
            with col_conv3:
                st.metric("CV (UPLS)", f"{conv['cv_upls']:.4f}")
            
            # Convergence chart (batch means)
            if conv.get('batch_means_upls') and len(conv['batch_means_upls']) > 1:
                st.markdown("#### Batch Mean Convergence")
                batch_data = {
                    'Batch': range(1, len(conv['batch_means_upls']) + 1),
                    'UPLS Mean': conv['batch_means_upls']
                }
                fig_conv = px.line(
                    batch_data,
                    x='Batch',
                    y='UPLS Mean',
                    markers=True,
                    title="UPLS Batch Means (should stabilize for convergence)"
                )
                fig_conv.update_layout(height=250)
                st.plotly_chart(fig_conv, use_container_width=True)
        
        st.markdown("---")
        
        # Worst-Case Scenarios
        if result.meta.get('worst_cases'):
            st.markdown("### Worst-Case Scenarios")
            worst_cases = result.meta['worst_cases']
            
            col_worst1, col_worst2 = st.columns(2)
            
            with col_worst1:
                st.markdown("#### Lowest UPLS Cases")
                for i, case in enumerate(worst_cases['lowest_upls'][:3], 1):
                    with st.expander(f"Case {i}: UPLS = {case['upls']:.3f}"):
                        st.write(f"**Decision**: {case['decision']}")
                        st.write(f"**Tripwire**: {case['tripwire']:.2f}")
                        st.write(f"**SV1a**: {case['sv1a']:.3f}")
                        st.write(f"**SV1b**: {case['sv1b']:.3f}")
                        st.write(f"**SV1c**: {case['sv1c']:.3f}")
            
            with col_worst2:
                st.markdown("#### Highest Tripwire Cases")
                for i, case in enumerate(worst_cases['highest_tripwire'][:3], 1):
                    with st.expander(f"Case {i}: Tripwire = {case['tripwire']:.2f}"):
                        st.write(f"**Decision**: {case['decision']}")
                        st.write(f"**UPLS**: {case['upls']:.3f}")
                        st.write(f"**SV1a**: {case['sv1a']:.3f}")
                        st.write(f"**SV1b**: {case['sv1b']:.3f}")
                        st.write(f"**SV1c**: {case['sv1c']:.3f}")
