"""Scenario table panel with export buttons."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st


def render_scenario_table(rows: list[dict]) -> None:
    st.subheader("Full Scenario Details")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="pricing_matrix.csv",
            mime="text/csv",
        )
    with c2:
        st.download_button(
            "Download JSON",
            data=json.dumps(rows, indent=2).encode("utf-8"),
            file_name="pricing_matrix.json",
            mime="application/json",
        )
