"""
Evidence View Tab — Shows supporting records for each investigation finding
"""
import streamlit as st
import pandas as pd


def render_evidence(investigations: list[dict], evidence_map: dict[str, list[dict]]):
    """Render the evidence chain tab."""

    st.header("📋 Evidence Chain")

    if not investigations:
        st.info("No investigations to show evidence for. Run analysis first.")
        return

    # Investigation selector
    inv_options = {
        f"{inv['id']} — {inv['title']} [{inv['priority'].upper()}]": inv["id"]
        for inv in investigations
    }
    selected_label = st.selectbox("Select Investigation", list(inv_options.keys()))
    selected_id = inv_options[selected_label]

    evidence_chain = evidence_map.get(selected_id, [])

    if not evidence_chain:
        st.warning("No evidence available for this investigation.")
        return

    st.caption(f"Showing {len(evidence_chain)} finding(s) with supporting evidence")

    for i, evidence in enumerate(evidence_chain):
        severity_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        icon = severity_colors.get(evidence.get("severity", ""), "📄")

        with st.expander(f"{icon} Finding {i + 1}: {evidence['finding']}", expanded=True):
            st.markdown(f"**Check:** `{evidence['check_name']}`")
            st.markdown(f"**Severity:** {evidence.get('severity', 'N/A')}")
            st.markdown(f"**Timestamp:** {evidence['timestamp']}")

            if evidence["supporting_records"]:
                st.markdown("**Supporting Records:**")

                # Group by source table
                by_table = {}
                for rec in evidence["supporting_records"]:
                    table = rec["source_table"]
                    if table not in by_table:
                        by_table[table] = []
                    by_table[table].append(rec["record"])

                for table, records in by_table.items():
                    st.markdown(f"*From `{table}`:*")
                    df = pd.DataFrame(records)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("No supporting records found in the dataset.")
