"""
Payment Investigation System - Configuration

All thresholds, constants, and API configuration.
"""
import os

# --- Gemini API ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# --- Thresholds ---
AMOUNT_TOLERANCE = 0.01  # ₹0.01 tolerance for float comparisons
CONFIDENCE_REVIEW_THRESHOLD = 0.7  # Below this → human review queue

# --- Anomaly Types ---
ANOMALY_TYPES = [
    "payment_order_mismatch",
    "missing_payment",
    "duplicate_payment",
    "missing_refund",
    "incorrect_refund_amount",
    "settlement_mismatch",
    "duplicate_settlement",
    "missing_settlement",
    "orphan_record",
]

# --- Severity Levels ---
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

# --- Priority Levels ---
PRIORITY_LEVELS = ["critical", "high", "medium", "low"]

# --- Data Generation ---
NUM_ORDERS = 200
ANOMALY_INJECTION_RATE = 0.17  # ~17% of records will have anomalies
