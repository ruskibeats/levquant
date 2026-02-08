"""Scenario heatmap panel."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_heatmap_panel(df: pd.DataFrame) -> None:
    st.subheader("What-If Scenarios (Green=Safe, Amber=Urgent, Red=Act Now)")

    posture_rank = {"NORMAL": 0, "URGENT": 1, "FORCE": 2}
    dfx = df.copy()
    dfx["posture_rank"] = dfx["posture"].map(posture_rank)
    dfx["Rule-Breaking Leverage (SV1b)"] = dfx["SV1b"]
    dfx["Right to Bring the Claim (SV1a)"] = dfx["SV1a"]
    dfx["Cost Pressure on Them (SV1c)"] = dfx["SV1c"]
    dfx["Position Strength"] = dfx["upls"]
    dfx["Pressure Level (0–10)"] = dfx["tripwire"]
    dfx["Aim Offer (£)"] = dfx["target_gbp"]
    dfx["Recommended Action"] = dfx["decision"]
    dfx["Stance"] = dfx["posture"]

    fig = px.density_heatmap(
        dfx,
        x="Rule-Breaking Leverage (SV1b)",
        y="Right to Bring the Claim (SV1a)",
        z="posture_rank",
        hover_data=[
            "Right to Bring the Claim (SV1a)",
            "Rule-Breaking Leverage (SV1b)",
            "Cost Pressure on Them (SV1c)",
            "Position Strength",
            "Pressure Level (0–10)",
            "Aim Offer (£)",
            "Recommended Action",
            "Stance",
        ],
        color_continuous_scale=[(0.0, "green"), (0.5, "orange"), (1.0, "red")],
        title="Stance Heatmap (Green=NORMAL, Amber=URGENT, Red=FORCE)",
    )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)
