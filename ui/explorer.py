"""
Transaction Explorer Tab — Searchable, filterable table of all transactions
"""
import streamlit as st
import pandas as pd


def render_explorer(data: dict[str, pd.DataFrame], anomalies: list[dict]):
    """Render the transaction explorer tab."""

    st.header("🔎 Transaction Explorer")

    if not data:
        st.info("No data loaded. Run analysis first.")
        return

    # Table selector
    table_name = st.selectbox("Select Table", list(data.keys()))
    df = data[table_name].copy()

    # Collect all anomalous record IDs
    anomalous_ids = set()
    for a in anomalies:
        anomalous_ids.update(a.get("record_ids", []))

    # Search filter
    search = st.text_input("🔍 Search records", placeholder="Search by ID, amount, status...")
    if search:
        mask = df.astype(str).apply(lambda row: row.str.contains(search, case=False).any(), axis=1)
        df = df[mask]

    # Mark anomalous rows
    id_cols = [c for c in df.columns if c.endswith("_id")]
    if id_cols:
        df["⚠️ Flagged"] = df.apply(
            lambda row: "🔴 Yes" if any(row.get(c) in anomalous_ids for c in id_cols) else "",
            axis=1,
        )

    # Show filter for flagged only
    show_flagged = st.checkbox("Show only flagged records")
    if show_flagged and "⚠️ Flagged" in df.columns:
        df = df[df["⚠️ Flagged"] != ""]

    st.caption(f"Showing {len(df)} record(s) from `{table_name}`")
    st.dataframe(df, use_container_width=True, hide_index=True, height=500)
