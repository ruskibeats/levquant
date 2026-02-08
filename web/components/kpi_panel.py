"""KPI panel renderer."""

from __future__ import annotations

import streamlit as st


def render_kpi_panel(priced: dict) -> None:
    engine = priced["engine"]
    posture = priced["posture"]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Position Strength", f"{engine.upls:.3f}")
    c2.metric("Recommended Action", engine.decision)
    c3.metric("Certainty Score", engine.confidence)
    c4.metric("Pressure Level (0–10)", f"{engine.tripwire:.2f}")
    c5.metric("Pressure Alert", "Triggered" if engine.tripwire_triggered else "Clear")
    c6.metric("Stance", posture)
