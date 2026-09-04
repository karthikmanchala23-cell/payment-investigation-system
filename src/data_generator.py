"""
Synthetic Data Generator

Generates realistic payment lifecycle data (orders, payments, refunds,
settlements, finance records) and injects known anomalies for testing.
"""
import json
import os
import random
import string
from datetime import datetime, timedelta

import pandas as pd

from config import NUM_ORDERS, ANOMALY_INJECTION_RATE


def _random_id(prefix: str, length: int = 14) -> str:
    """Generate a realistic-looking ID like 'order_AbC12xYz90pQ'."""
    chars = string.ascii_letters + string.digits
    return f"{prefix}_{''.join(random.choices(chars, k=length))}"


def _random_amount(low: float = 100.0, high: float = 50000.0) -> float:
    """Generate a random payment amount rounded to 2 decimals."""
    return round(random.uniform(low, high), 2)


def generate_data(num_orders: int = NUM_ORDERS, seed: int = 42) -> dict:
    """
    Generate a complete synthetic payment lifecycle dataset.

    Returns:
        dict with keys: 'orders', 'payments', 'refunds', 'settlements',
        'finance_records' (DataFrames), and 'ground_truth' (list of dicts).
    """
    random.seed(seed)
    ground_truth = []
    base_date = datetime(2026, 1, 1)

    # --- Step 1: Generate clean base data ---
    orders = []
    payments = []
    refunds = []
    settlement_entries = []  # individual payment-to-settlement links
    finance_records = []

    for i in range(num_orders):
        order_id = _random_id("ord")
        amount = _random_amount()
        order_date = base_date + timedelta(hours=random.randint(0, 2000))

        orders.append({
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "status": "paid",
            "created_at": order_date.isoformat(),
        })

        # Payment for this order
        payment_id = _random_id("pay")
        payment_date = order_date + timedelta(minutes=random.randint(1, 30))
        payments.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "status": "captured",
            "method": random.choice(["upi", "card", "netbanking", "wallet"]),
            "created_at": payment_date.isoformat(),
        })

        # ~20% of orders get a refund
        if random.random() < 0.20:
            refund_id = _random_id("rfnd")
            refund_amount = amount  # full refund by default
            refund_date = payment_date + timedelta(hours=random.randint(1, 48))
            refunds.append({
                "refund_id": refund_id,
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": refund_amount,
                "status": "processed",
                "created_at": refund_date.isoformat(),
            })

        # Settlement entry
        batch_id = f"batch_{(i // 10) + 1:04d}"
        settlement_entries.append({
            "settlement_id": _random_id("stl"),
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "batch_id": batch_id,
            "status": "settled",
            "settled_at": (payment_date + timedelta(days=random.randint(1, 3))).isoformat(),
        })

        # Finance record
        finance_records.append({
            "finance_id": _random_id("fin"),
            "payment_id": payment_id,
            "order_id": order_id,
            "type": "credit",
            "amount": amount,
            "created_at": payment_date.isoformat(),
        })

    # --- Step 2: Inject anomalies ---
    num_anomalies = int(num_orders * ANOMALY_INJECTION_RATE)
    anomaly_indices = random.sample(range(num_orders), min(num_anomalies, num_orders))

    anomaly_types = [
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

    for idx in anomaly_indices:
        anomaly_type = random.choice(anomaly_types)
        order = orders[idx]
        payment = payments[idx]

        if anomaly_type == "payment_order_mismatch":
            # Alter payment amount so it doesn't match order
            diff = round(random.uniform(50, 500), 2)
            payments[idx]["amount"] = round(payment["amount"] + diff, 2)
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [order["order_id"], payment["payment_id"]],
                "details": f"Payment amount {payments[idx]['amount']} != order amount {order['amount']}",
            })

        elif anomaly_type == "missing_payment":
            # Remove the payment for this order
            payments[idx]["_deleted"] = True
            orders[idx]["status"] = "created"  # order never got paid
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [order["order_id"]],
                "details": f"Order {order['order_id']} has no payment",
            })
            # Also remove settlement for this payment
            settlement_entries[idx]["_deleted"] = True

        elif anomaly_type == "duplicate_payment":
            # Add a duplicate payment for the same order
            dup_payment = payment.copy()
            dup_payment["payment_id"] = _random_id("pay")
            dup_payment["amount"] = payment["amount"]
            payments.append(dup_payment)
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [order["order_id"], payment["payment_id"], dup_payment["payment_id"]],
                "details": f"Order {order['order_id']} has duplicate payments",
            })

        elif anomaly_type == "missing_refund":
            # Mark order as refund-expected but don't create one
            # Remove any existing refund for this payment
            refunds = [r for r in refunds if r.get("payment_id") != payment["payment_id"]]
            orders[idx]["status"] = "refund_expected"
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [order["order_id"], payment["payment_id"]],
                "details": f"Order {order['order_id']} marked for refund but none exists",
            })

        elif anomaly_type == "incorrect_refund_amount":
            # Find or create a refund, then alter its amount
            existing = [r for r in refunds if r.get("payment_id") == payment["payment_id"]]
            if existing:
                diff = round(random.uniform(10, 200), 2)
                existing[0]["amount"] = round(existing[0]["amount"] - diff, 2)
                ground_truth.append({
                    "type": anomaly_type,
                    "record_ids": [existing[0]["refund_id"], payment["payment_id"]],
                    "details": f"Refund amount {existing[0]['amount']} != payment amount {payment['amount']}",
                })
            else:
                # Create a refund with wrong amount
                refund_id = _random_id("rfnd")
                wrong_amount = round(payment["amount"] - random.uniform(10, 200), 2)
                refunds.append({
                    "refund_id": refund_id,
                    "payment_id": payment["payment_id"],
                    "order_id": order["order_id"],
                    "amount": wrong_amount,
                    "status": "processed",
                    "created_at": payment["created_at"],
                })
                ground_truth.append({
                    "type": anomaly_type,
                    "record_ids": [refund_id, payment["payment_id"]],
                    "details": f"Refund amount {wrong_amount} != payment amount {payment['amount']}",
                })

        elif anomaly_type == "settlement_mismatch":
            # Alter settlement amount
            diff = round(random.uniform(50, 300), 2)
            settlement_entries[idx]["amount"] = round(
                settlement_entries[idx]["amount"] + diff, 2
            )
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [settlement_entries[idx]["settlement_id"], payment["payment_id"]],
                "details": f"Settlement amount {settlement_entries[idx]['amount']} != payment amount {payment['amount']}",
            })

        elif anomaly_type == "duplicate_settlement":
            # Duplicate this settlement entry in a different batch
            dup_stl = settlement_entries[idx].copy()
            dup_stl["settlement_id"] = _random_id("stl")
            dup_stl["batch_id"] = f"batch_{random.randint(9000, 9999):04d}"
            settlement_entries.append(dup_stl)
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [
                    settlement_entries[idx]["settlement_id"],
                    dup_stl["settlement_id"],
                    payment["payment_id"],
                ],
                "details": f"Payment {payment['payment_id']} settled in multiple batches",
            })

        elif anomaly_type == "missing_settlement":
            # Remove the settlement for this payment
            settlement_entries[idx]["_deleted"] = True
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [payment["payment_id"]],
                "details": f"Payment {payment['payment_id']} has no settlement",
            })

        elif anomaly_type == "orphan_record":
            # Create a refund that references a non-existent payment
            orphan_payment_id = _random_id("pay")
            orphan_refund_id = _random_id("rfnd")
            refunds.append({
                "refund_id": orphan_refund_id,
                "payment_id": orphan_payment_id,
                "order_id": _random_id("ord"),
                "amount": _random_amount(100, 5000),
                "status": "processed",
                "created_at": (base_date + timedelta(hours=random.randint(0, 2000))).isoformat(),
            })
            ground_truth.append({
                "type": anomaly_type,
                "record_ids": [orphan_refund_id, orphan_payment_id],
                "details": f"Refund {orphan_refund_id} references non-existent payment {orphan_payment_id}",
            })

    # --- Step 3: Filter out deleted records and build DataFrames ---
    payments = [p for p in payments if not p.get("_deleted")]
    settlement_entries = [s for s in settlement_entries if not s.get("_deleted")]

    # Build settlement summary (one row per batch)
    batch_totals = {}
    for s in settlement_entries:
        bid = s["batch_id"]
        if bid not in batch_totals:
            batch_totals[bid] = {"batch_id": bid, "total_amount": 0.0, "payment_count": 0, "settled_at": s["settled_at"]}
        batch_totals[bid]["total_amount"] = round(batch_totals[bid]["total_amount"] + s["amount"], 2)
        batch_totals[bid]["payment_count"] += 1

    result = {
        "orders": pd.DataFrame(orders),
        "payments": pd.DataFrame(payments),
        "refunds": pd.DataFrame(refunds) if refunds else pd.DataFrame(columns=["refund_id", "payment_id", "order_id", "amount", "status", "created_at"]),
        "settlements": pd.DataFrame(settlement_entries),
        "finance_records": pd.DataFrame(finance_records),
        "ground_truth": ground_truth,
    }
    return result


def save_sample_data(output_dir: str = "data/sample") -> dict:
    """Generate and save sample data to CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    data = generate_data()

    data["orders"].to_csv(os.path.join(output_dir, "orders.csv"), index=False)
    data["payments"].to_csv(os.path.join(output_dir, "payments.csv"), index=False)
    data["refunds"].to_csv(os.path.join(output_dir, "refunds.csv"), index=False)
    data["settlements"].to_csv(os.path.join(output_dir, "settlements.csv"), index=False)
    data["finance_records"].to_csv(os.path.join(output_dir, "finance_records.csv"), index=False)

    gt_path = os.path.join(output_dir, "..", "ground_truth.json")
    with open(gt_path, "w") as f:
        json.dump(data["ground_truth"], f, indent=2)

    return data


if __name__ == "__main__":
    save_sample_data()
    print("Sample data generated successfully.")
