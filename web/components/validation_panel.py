"""Validation battery panel."""

from __future__ import annotations

import streamlit as st


def render_validation_panel(validation_rows: list[dict]) -> None:
    st.subheader("Safety Checks")
    passed = sum(1 for r in validation_rows if r["passed"])
    failed = len(validation_rows) - passed
    st.info(f"Checks passed: {passed} | failed: {failed}")

    for row in validation_rows:
        icon = "✅" if row["passed"] else "❌"
        with st.expander(f"{icon} {row['name']}"):
            st.write(f"Expected result: {row['expected']}")
            st.write(f"Actual result: {row['actual']}")
            st.write(f"Why this check exists: {row['rationale']}")
            st.write(f"Deviation flag: {row['deviation_flag']}")
