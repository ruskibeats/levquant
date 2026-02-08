"""Settlement corridor panel."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def render_corridor_panel(priced: dict) -> None:
    corridor = priced["corridor"]
    fear = priced["fear_index"]
    active_kill_switches = priced["kill_switches_active"]

    st.subheader("Settlement Range (GBP)")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[corridor.floor_gbp, corridor.base_case_gbp, corridor.target_gbp, corridor.ceiling_gbp],
            y=["Range", "Range", "Range", "Range"],
            mode="lines+markers+text",
            text=["Minimum Offer", "Likely Offer", "Aim Offer", "Maximum Offer"],
            textposition="top center",
            line={"width": 10},
            marker={"size": 12},
            name="Settlement range",
        )
    )
    fig.update_layout(height=220, margin={"l": 10, "r": 10, "t": 10, "b": 10}, xaxis_title="GBP")
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Increase vs minimum offer: {corridor.delta_vs_floor_pct:.2f}%")
    st.caption("Assumptions are explicit in the 'What This Is Based On' panel.")

    if fear > 0 or active_kill_switches:
        st.warning(
            "Range adjusted for weakest-link stress and events that change everything | "
            f"Weakest-Link Stress Level={fear:.2f}, active events={len(active_kill_switches)}"
        )
