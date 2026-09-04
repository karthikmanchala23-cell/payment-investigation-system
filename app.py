"""
Payment Investigation System — Streamlit App

Main entry point. Orchestrates data loading, analysis, and rendering.
"""
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import json

from src.data_generator import save_sample_data
from src.data_loader import load_sample_data, load_csvs
from src.anomaly_detector import run_all_checks
from src.investigator import group_into_investigations
from src.gemini_analyzer import enrich_investigations
from src.evidence import build_all_evidence
from src.evaluator import load_ground_truth, evaluate
from src.audit import create_audit_log, log_analysis_run
from ui.dashboard import render_dashboard
from ui.investigation_view import render_investigations
from ui.evidence_view import render_evidence
from ui.explorer import render_explorer


# --- Page Config ---
st.set_page_config(
    page_title="Payment Investigation System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* KPI / Metric cards: light background with dark text */
    .stMetric {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
    }
    /* Force dark text on all metric elements (label, value, delta) */
    .stMetric label,
    .stMetric div,
    .stMetric p,
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricDelta"] {
        color: #1a1a2e !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 500;
        opacity: 0.85;
    }
    /* Expander border */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --- Session State Init ---
if "audit_log" not in st.session_state:
    st.session_state.audit_log = create_audit_log()
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False


def run_analysis(data: dict, ground_truth: list | None = None):
    """Run the full analysis pipeline."""
    with st.spinner("Running deterministic anomaly checks..."):
        anomalies = run_all_checks(data)

    with st.spinner("Grouping anomalies into investigations..."):
        investigations = group_into_investigations(anomalies)

    with st.spinner("Running AI analysis (advisory)..."):
        investigations = enrich_investigations(investigations)

    with st.spinner("Building evidence chains..."):
        evidence_map = build_all_evidence(investigations, data)

    eval_results = None
    if ground_truth:
        with st.spinner("Evaluating against ground truth..."):
            eval_results = evaluate(anomalies, ground_truth)

    # Log to audit trail
    log_analysis_run(st.session_state.audit_log, len(anomalies), len(investigations))

    # Store in session
    st.session_state.data = data
    st.session_state.anomalies = anomalies
    st.session_state.investigations = investigations
    st.session_state.evidence_map = evidence_map
    st.session_state.eval_results = eval_results
    st.session_state.analysis_done = True


# --- Sidebar ---
with st.sidebar:
    st.title("🔍 Payment Investigation")
    st.caption("AI Finance Controller · Razorpay Buildathon")
    st.divider()

    data_source = st.radio("Data Source", ["📦 Sample Data", "📁 Upload CSVs"])

    if data_source == "📦 Sample Data":
        if st.button("🚀 Generate & Analyze", use_container_width=True):
            with st.spinner("Generating synthetic data..."):
                save_sample_data()
            data, errors = load_sample_data()
            if errors:
                st.error(f"Data errors: {errors}")
            else:
                try:
                    gt = load_ground_truth()
                except Exception:
                    gt = None
                run_analysis(data, gt)
                st.success(f"✅ Analysis complete!")

    else:
        st.markdown("Upload your CSV files:")
        orders_file = st.file_uploader("Orders", type="csv", key="orders")
        payments_file = st.file_uploader("Payments", type="csv", key="payments")
        refunds_file = st.file_uploader("Refunds", type="csv", key="refunds")
        settlements_file = st.file_uploader("Settlements", type="csv", key="settlements")
        finance_file = st.file_uploader("Finance Records", type="csv", key="finance")

        if st.button("🚀 Analyze Uploaded Data", use_container_width=True):
            file_dict = {}
            if orders_file:
                file_dict["orders"] = orders_file
            if payments_file:
                file_dict["payments"] = payments_file
            if refunds_file:
                file_dict["refunds"] = refunds_file
            if settlements_file:
                file_dict["settlements"] = settlements_file
            if finance_file:
                file_dict["finance_records"] = finance_file

            if len(file_dict) < 4:
                st.error("Please upload at least Orders, Payments, Refunds, and Settlements.")
            else:
                data, errors = load_csvs(file_dict)
                if errors:
                    st.error(f"Validation errors: {errors}")
                else:
                    run_analysis(data)
                    st.success(f"✅ Analysis complete!")

    # Audit trail download
    if st.session_state.audit_log:
        st.divider()
        st.download_button(
            "📥 Download Audit Trail",
            data=json.dumps(st.session_state.audit_log, indent=2),
            file_name="audit_trail.json",
            mime="application/json",
            use_container_width=True,
        )


# --- Main Content ---
if st.session_state.analysis_done:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🔍 Investigations",
        "📋 Evidence",
        "🔎 Explorer",
    ])

    with tab1:
        render_dashboard(
            st.session_state.investigations,
            st.session_state.anomalies,
            st.session_state.eval_results,
            st.session_state.data,
        )

    with tab2:
        render_investigations(
            st.session_state.investigations,
            st.session_state.audit_log,
        )

    with tab3:
        render_evidence(
            st.session_state.investigations,
            st.session_state.evidence_map,
        )

    with tab4:
        render_explorer(
            st.session_state.data,
            st.session_state.anomalies,
        )
else:
    st.title("🔍 Payment Investigation System")
    st.markdown("""
    ### Welcome!
    
    This system analyzes payment lifecycle data to detect anomalies,
    group them into investigations, and identify potential root causes.
    
    **Get started:**
    1. Use the sidebar to select a data source
    2. Click **Generate & Analyze** for sample data, or upload your own CSVs
    3. Explore the results across the four tabs
    
    ---
    
    **Key Features:**
    - 🔬 **9 Deterministic Checks** — objective financial fact verification
    - 🔗 **Investigation Grouping** — related anomalies merged via entity linking
    - 🤖 **AI Root-Cause Analysis** — Gemini provides advisory hypotheses (never overrides facts)
    - 📋 **Evidence Chains** — full source record traceability
    - ✅ **Human Review** — accept/reject workflow for uncertain findings
    - 📊 **Ground-Truth Evaluation** — precision, recall, F1 metrics
    """)
