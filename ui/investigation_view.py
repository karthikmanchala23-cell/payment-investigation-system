"""
Investigation View Tab — Investigation details with review actions
"""
import streamlit as st

from src.review import accept_investigation, reject_investigation
from src.audit import log_review


PRIORITY_COLORS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

STATUS_BADGES = {
    "open": "🔵 Open",
    "accepted": "✅ Accepted",
    "rejected": "❌ Rejected",
}


def render_investigations(investigations: list[dict], audit_log: list):
    """Render the investigation details tab."""

    st.header("🔍 Investigations")

    if not investigations:
        st.info("No investigations found. Run analysis first.")
        return

    # Summary counts
    open_count = sum(1 for inv in investigations if inv["status"] == "open")
    st.caption(f"{len(investigations)} investigations total · {open_count} open")

    for inv in investigations:
        priority_icon = PRIORITY_COLORS.get(inv["priority"], "⚪")
        status_badge = STATUS_BADGES.get(inv["status"], inv["status"])

        with st.expander(
            f"{priority_icon} {inv['id']} — {inv['title']} [{inv['priority'].upper()}] {status_badge}",
            expanded=inv["status"] == "open" and inv["priority"] in ("critical", "high"),
        ):
            # Investigation metadata
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            meta_col1.metric("Priority", inv["priority"].upper())
            meta_col2.metric("Confidence", f"{inv['confidence']:.0%}")
            meta_col3.metric("Amount Affected", f"₹{inv['total_amount_affected']:,.2f}")

            # Anomaly types
            st.markdown(f"**Anomaly Types:** {', '.join(inv['anomaly_types'])}")
            st.markdown(f"**Related Records:** {len(inv['record_ids'])} records")

            # Individual anomalies
            st.markdown("---")
            st.markdown("**Anomaly Details:**")
            for i, anomaly in enumerate(inv["anomalies"]):
                severity_map = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                icon = severity_map.get(anomaly["severity"], "⚪")
                st.markdown(f"{icon} **{anomaly['type']}** ({anomaly['severity']}): {anomaly['details']}")

            # AI Analysis
            st.markdown("---")
            if inv.get("ai_analysis"):
                st.markdown("**🤖 AI Analysis** *(advisory only — does not override findings)*")
                ai = inv["ai_analysis"]
                st.markdown(f"**Hypothesis:** {ai.get('root_cause_hypothesis', 'N/A')}")
                st.markdown(f"**Explanation:** {ai.get('explanation', 'N/A')}")
                st.markdown(f"**Recommended Action:** {ai.get('recommended_action', 'N/A')}")

            # Review actions
            if inv["status"] == "open":
                st.markdown("---")
                st.markdown("**Review Actions:**")
                comment = st.text_input(
                    "Comment (optional)", key=f"comment_{inv['id']}", label_visibility="collapsed",
                    placeholder="Add a comment...",
                )
                btn_col1, btn_col2, _ = st.columns([1, 1, 3])
                with btn_col1:
                    if st.button("✅ Accept", key=f"accept_{inv['id']}"):
                        accept_investigation(inv, comment=comment)
                        log_review(audit_log, inv["id"], "accepted", "analyst", comment)
                        st.rerun()
                with btn_col2:
                    if st.button("❌ Reject", key=f"reject_{inv['id']}"):
                        reject_investigation(inv, comment=comment)
                        log_review(audit_log, inv["id"], "rejected", "analyst", comment)
                        st.rerun()
