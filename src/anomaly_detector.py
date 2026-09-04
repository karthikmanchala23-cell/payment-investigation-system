"""
Deterministic Anomaly Detector

Pure-logic checks for financial anomalies. No AI involvement.
Each check function returns a list of Anomaly dicts.
"""
import pandas as pd

from config import AMOUNT_TOLERANCE, SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW


def _anomaly(atype: str, severity: str, record_ids: list, details: str, evidence: dict = None) -> dict:
    """Create a standardized anomaly dict."""
    return {
        "type": atype,
        "severity": severity,
        "record_ids": record_ids,
        "details": details,
        "evidence": evidence or {},
    }


def check_payment_order_mismatch(orders: pd.DataFrame, payments: pd.DataFrame) -> list[dict]:
    """Detect payments whose amount doesn't match their order."""
    anomalies = []
    merged = payments.merge(orders, on="order_id", suffixes=("_pay", "_ord"))
    for _, row in merged.iterrows():
        diff = abs(row["amount_pay"] - row["amount_ord"])
        if diff > AMOUNT_TOLERANCE:
            anomalies.append(_anomaly(
                "payment_order_mismatch", SEVERITY_HIGH,
                [row["order_id"], row["payment_id"]],
                f"Payment amount ₹{row['amount_pay']} != Order amount ₹{row['amount_ord']} (diff: ₹{diff:.2f})",
                {"payment_amount": row["amount_pay"], "order_amount": row["amount_ord"], "difference": round(diff, 2)},
            ))
    return anomalies


def check_missing_payment(orders: pd.DataFrame, payments: pd.DataFrame) -> list[dict]:
    """Detect orders with no corresponding payment."""
    anomalies = []
    paid_orders = set(payments["order_id"].unique())
    for _, row in orders.iterrows():
        if row["order_id"] not in paid_orders:
            anomalies.append(_anomaly(
                "missing_payment", SEVERITY_CRITICAL,
                [row["order_id"]],
                f"Order {row['order_id']} (₹{row['amount']}) has no payment record",
                {"order_amount": row["amount"], "order_status": row.get("status", "unknown")},
            ))
    return anomalies


def check_duplicate_payment(payments: pd.DataFrame) -> list[dict]:
    """Detect multiple payments for the same order."""
    anomalies = []
    dup_groups = payments.groupby("order_id").filter(lambda g: len(g) > 1)
    if not dup_groups.empty:
        for order_id, group in dup_groups.groupby("order_id"):
            pay_ids = group["payment_id"].tolist()
            total = group["amount"].sum()
            anomalies.append(_anomaly(
                "duplicate_payment", SEVERITY_HIGH,
                [order_id] + pay_ids,
                f"Order {order_id} has {len(pay_ids)} payments totalling ₹{total:.2f}",
                {"payment_ids": pay_ids, "amounts": group["amount"].tolist()},
            ))
    return anomalies


def check_missing_refund(orders: pd.DataFrame, refunds: pd.DataFrame) -> list[dict]:
    """Detect orders expecting a refund but none exists."""
    anomalies = []
    refunded_orders = set(refunds["order_id"].unique()) if not refunds.empty else set()
    refund_expected = orders[orders["status"] == "refund_expected"]
    for _, row in refund_expected.iterrows():
        if row["order_id"] not in refunded_orders:
            anomalies.append(_anomaly(
                "missing_refund", SEVERITY_HIGH,
                [row["order_id"]],
                f"Order {row['order_id']} is marked refund_expected but no refund exists",
                {"order_status": row["status"]},
            ))
    return anomalies


def check_incorrect_refund_amount(payments: pd.DataFrame, refunds: pd.DataFrame) -> list[dict]:
    """Detect refunds whose amount doesn't match the payment amount."""
    anomalies = []
    if refunds.empty:
        return anomalies
    merged = refunds.merge(payments[["payment_id", "amount"]], on="payment_id", suffixes=("_rfnd", "_pay"))
    for _, row in merged.iterrows():
        diff = abs(row["amount_rfnd"] - row["amount_pay"])
        if diff > AMOUNT_TOLERANCE:
            anomalies.append(_anomaly(
                "incorrect_refund_amount", SEVERITY_MEDIUM,
                [row["refund_id"], row["payment_id"]],
                f"Refund amount ₹{row['amount_rfnd']} != Payment amount ₹{row['amount_pay']} (diff: ₹{diff:.2f})",
                {"refund_amount": row["amount_rfnd"], "payment_amount": row["amount_pay"]},
            ))
    return anomalies


def check_settlement_mismatch(payments: pd.DataFrame, settlements: pd.DataFrame) -> list[dict]:
    """Detect settlements where amount doesn't match the payment amount."""
    anomalies = []
    merged = settlements.merge(payments[["payment_id", "amount"]], on="payment_id", suffixes=("_stl", "_pay"))
    for _, row in merged.iterrows():
        diff = abs(row["amount_stl"] - row["amount_pay"])
        if diff > AMOUNT_TOLERANCE:
            anomalies.append(_anomaly(
                "settlement_mismatch", SEVERITY_HIGH,
                [row["settlement_id"], row["payment_id"]],
                f"Settlement amount ₹{row['amount_stl']} != Payment amount ₹{row['amount_pay']}",
                {"settlement_amount": row["amount_stl"], "payment_amount": row["amount_pay"]},
            ))
    return anomalies


def check_duplicate_settlement(settlements: pd.DataFrame) -> list[dict]:
    """Detect payments that appear in multiple settlement batches."""
    anomalies = []
    dup_groups = settlements.groupby("payment_id").filter(lambda g: g["batch_id"].nunique() > 1)
    if not dup_groups.empty:
        for pay_id, group in dup_groups.groupby("payment_id"):
            stl_ids = group["settlement_id"].tolist()
            batches = group["batch_id"].unique().tolist()
            anomalies.append(_anomaly(
                "duplicate_settlement", SEVERITY_CRITICAL,
                [pay_id] + stl_ids,
                f"Payment {pay_id} settled in {len(batches)} batches: {batches}",
                {"settlement_ids": stl_ids, "batches": batches},
            ))
    return anomalies


def check_missing_settlement(payments: pd.DataFrame, settlements: pd.DataFrame) -> list[dict]:
    """Detect captured payments with no settlement."""
    anomalies = []
    settled_payments = set(settlements["payment_id"].unique())
    captured = payments[payments["status"] == "captured"]
    for _, row in captured.iterrows():
        if row["payment_id"] not in settled_payments:
            anomalies.append(_anomaly(
                "missing_settlement", SEVERITY_HIGH,
                [row["payment_id"]],
                f"Captured payment {row['payment_id']} (₹{row['amount']}) has no settlement",
                {"payment_amount": row["amount"]},
            ))
    return anomalies


def check_orphan_records(payments: pd.DataFrame, refunds: pd.DataFrame, orders: pd.DataFrame) -> list[dict]:
    """Detect records referencing non-existent parents."""
    anomalies = []
    order_ids = set(orders["order_id"].unique())
    payment_ids = set(payments["payment_id"].unique())

    # Payments referencing non-existent orders
    for _, row in payments.iterrows():
        if row["order_id"] not in order_ids:
            anomalies.append(_anomaly(
                "orphan_record", SEVERITY_MEDIUM,
                [row["payment_id"], row["order_id"]],
                f"Payment {row['payment_id']} references non-existent order {row['order_id']}",
                {"orphan_type": "payment_missing_order"},
            ))

    # Refunds referencing non-existent payments
    if not refunds.empty:
        for _, row in refunds.iterrows():
            if row["payment_id"] not in payment_ids:
                anomalies.append(_anomaly(
                    "orphan_record", SEVERITY_MEDIUM,
                    [row["refund_id"], row["payment_id"]],
                    f"Refund {row['refund_id']} references non-existent payment {row['payment_id']}",
                    {"orphan_type": "refund_missing_payment"},
                ))

    return anomalies


def run_all_checks(data: dict[str, pd.DataFrame]) -> list[dict]:
    """Run all 9 deterministic checks and return combined anomaly list."""
    orders = data["orders"]
    payments = data["payments"]
    refunds = data["refunds"]
    settlements = data["settlements"]

    anomalies = []
    anomalies.extend(check_payment_order_mismatch(orders, payments))
    anomalies.extend(check_missing_payment(orders, payments))
    anomalies.extend(check_duplicate_payment(payments))
    anomalies.extend(check_missing_refund(orders, refunds))
    anomalies.extend(check_incorrect_refund_amount(payments, refunds))
    anomalies.extend(check_settlement_mismatch(payments, settlements))
    anomalies.extend(check_duplicate_settlement(settlements))
    anomalies.extend(check_missing_settlement(payments, settlements))
    anomalies.extend(check_orphan_records(payments, refunds, orders))

    return anomalies
