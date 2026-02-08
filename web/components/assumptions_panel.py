"""Assumptions and audit renderer."""

from __future__ import annotations

import streamlit as st


def render_assumptions_panel(assumptions: dict, audit_bundle: dict) -> None:
    st.subheader("What This Is Based On")
    st.caption("These assumptions are listed so the numbers can be challenged, not hidden.")
    st.json(
        {
            "timestamp_utc": audit_bundle["timestamp_utc"],
            "model_version": audit_bundle["model_version"],
            "input_hash": audit_bundle["input_hash"],
            "assumptions": assumptions,
        }
    )
