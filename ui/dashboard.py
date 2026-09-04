"""
Dashboard Tab — Overview metrics and charts
"""
import streamlit as st
import plotly.express as px
import pandas as pd


def render_dashboard(investigations: list[dict], anomalies: list[dict],
                     eval_results: dict | None, data: dict[str, pd.DataFrame]):
    """Render the overview dashboard tab."""

    st.header("📊 Dashboard")

    # --- KPI Cards ---
    total_transactions = sum(len(df) for df in data.values())
    total_anomalies = len(anomalies)
    total_investigations = len(investigations)
    avg_confidence = (
        sum(inv["confidence"] for inv in investigations) / total_investigations
        if total_investigations > 0 else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", f"{total_transactions:,}")
    col2.metric("Anomalies Found", total_anomalies)
    col3.metric("Investigations", total_investigations)
    col4.metric("Avg Confidence", f"{avg_confidence:.0%}")

    st.divider()

    # --- Charts ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if anomalies:
            type_counts = pd.DataFrame(anomalies)["type"].value_counts().reset_index()
            type_counts.columns = ["Anomaly Type", "Count"]
            fig = px.bar(
                type_counts, x="Anomaly Type", y="Count",
                title="Anomalies by Type",
                color="Count", color_continuous_scale="Reds",
            )
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        if investigations:
            priority_counts = pd.DataFrame(investigations)["priority"].value_counts().reset_index()
            priority_counts.columns = ["Priority", "Count"]
            color_map = {"critical": "#dc3545", "high": "#fd7e14", "medium": "#ffc107", "low": "#28a745"}
            fig = px.pie(
                priority_counts, names="Priority", values="Count",
                title="Investigations by Priority",
                color="Priority", color_discrete_map=color_map,
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    # --- Evaluation Metrics ---
    if eval_results:
        st.subheader("🎯 Detection Accuracy (vs Ground Truth)")
        overall = eval_results["overall"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Precision", f"{overall['precision']:.1%}")
        m2.metric("Recall", f"{overall['recall']:.1%}")
        m3.metric("F1 Score", f"{overall['f1']:.1%}")

        if eval_results.get("per_type"):
            st.markdown("**Per-Type Breakdown:**")
            per_type_df = pd.DataFrame(eval_results["per_type"]).T
            per_type_df.index.name = "Anomaly Type"
            st.dataframe(per_type_df, use_container_width=True)
