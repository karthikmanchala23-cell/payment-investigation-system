"""
Tests for Anomaly Detector — all 9 deterministic checks
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest

from src.anomaly_detector import (
    check_payment_order_mismatch,
    check_missing_payment,
    check_duplicate_payment,
    check_missing_refund,
    check_incorrect_refund_amount,
    check_settlement_mismatch,
    check_duplicate_settlement,
    check_missing_settlement,
    check_orphan_records,
    run_all_checks,
)


@pytest.fixture
def sample_orders():
    return pd.DataFrame([
        {"order_id": "ord_1", "amount": 1000.00, "currency": "INR", "status": "paid", "created_at": "2026-01-01"},
        {"order_id": "ord_2", "amount": 2000.00, "currency": "INR", "status": "paid", "created_at": "2026-01-02"},
        {"order_id": "ord_3", "amount": 500.00, "currency": "INR", "status": "refund_expected", "created_at": "2026-01-03"},
    ])


@pytest.fixture
def sample_payments():
    return pd.DataFrame([
        {"payment_id": "pay_1", "order_id": "ord_1", "amount": 1000.00, "currency": "INR", "status": "captured", "method": "upi", "created_at": "2026-01-01"},
        {"payment_id": "pay_2", "order_id": "ord_2", "amount": 2000.00, "currency": "INR", "status": "captured", "method": "card", "created_at": "2026-01-02"},
        {"payment_id": "pay_3", "order_id": "ord_3", "amount": 500.00, "currency": "INR", "status": "captured", "method": "upi", "created_at": "2026-01-03"},
    ])


def test_payment_order_mismatch(sample_orders):
    payments = pd.DataFrame([
        {"payment_id": "pay_1", "order_id": "ord_1", "amount": 1100.00, "currency": "INR", "status": "captured", "method": "upi", "created_at": "2026-01-01"},
        {"payment_id": "pay_2", "order_id": "ord_2", "amount": 2000.00, "currency": "INR", "status": "captured", "method": "card", "created_at": "2026-01-02"},
    ])
    result = check_payment_order_mismatch(sample_orders, payments)
    assert len(result) == 1
    assert result[0]["type"] == "payment_order_mismatch"
    assert "ord_1" in result[0]["record_ids"]


def test_no_mismatch_within_tolerance(sample_orders):
    payments = pd.DataFrame([
        {"payment_id": "pay_1", "order_id": "ord_1", "amount": 1000.005, "currency": "INR", "status": "captured", "method": "upi", "created_at": "2026-01-01"},
    ])
    result = check_payment_order_mismatch(sample_orders, payments)
    assert len(result) == 0


def test_missing_payment(sample_orders, sample_payments):
    # Remove payment for ord_2
    payments = sample_payments[sample_payments["order_id"] != "ord_2"]
    result = check_missing_payment(sample_orders, payments)
    assert len(result) == 1
    assert result[0]["type"] == "missing_payment"
    assert "ord_2" in result[0]["record_ids"]


def test_duplicate_payment(sample_payments):
    dup = sample_payments.copy()
    extra = pd.DataFrame([
        {"payment_id": "pay_dup", "order_id": "ord_1", "amount": 1000.00, "currency": "INR", "status": "captured", "method": "card", "created_at": "2026-01-01"},
    ])
    payments = pd.concat([dup, extra], ignore_index=True)
    result = check_duplicate_payment(payments)
    assert len(result) == 1
    assert result[0]["type"] == "duplicate_payment"


def test_missing_refund(sample_orders):
    # ord_3 has status=refund_expected but no refund
    refunds = pd.DataFrame(columns=["refund_id", "payment_id", "order_id", "amount", "status", "created_at"])
    result = check_missing_refund(sample_orders, refunds)
    assert len(result) == 1
    assert result[0]["type"] == "missing_refund"
    assert "ord_3" in result[0]["record_ids"]


def test_incorrect_refund_amount(sample_payments):
    refunds = pd.DataFrame([
        {"refund_id": "rfnd_1", "payment_id": "pay_1", "order_id": "ord_1", "amount": 800.00, "status": "processed", "created_at": "2026-01-01"},
    ])
    result = check_incorrect_refund_amount(sample_payments, refunds)
    assert len(result) == 1
    assert result[0]["type"] == "incorrect_refund_amount"


def test_settlement_mismatch(sample_payments):
    settlements = pd.DataFrame([
        {"settlement_id": "stl_1", "payment_id": "pay_1", "order_id": "ord_1", "amount": 1200.00, "batch_id": "batch_001", "status": "settled", "settled_at": "2026-01-02"},
    ])
    result = check_settlement_mismatch(sample_payments, settlements)
    assert len(result) == 1
    assert result[0]["type"] == "settlement_mismatch"


def test_duplicate_settlement():
    settlements = pd.DataFrame([
        {"settlement_id": "stl_1", "payment_id": "pay_1", "order_id": "ord_1", "amount": 1000.00, "batch_id": "batch_001", "status": "settled", "settled_at": "2026-01-02"},
        {"settlement_id": "stl_2", "payment_id": "pay_1", "order_id": "ord_1", "amount": 1000.00, "batch_id": "batch_002", "status": "settled", "settled_at": "2026-01-03"},
    ])
    result = check_duplicate_settlement(settlements)
    assert len(result) == 1
    assert result[0]["type"] == "duplicate_settlement"


def test_missing_settlement(sample_payments):
    settlements = pd.DataFrame([
        {"settlement_id": "stl_1", "payment_id": "pay_1", "order_id": "ord_1", "amount": 1000.00, "batch_id": "batch_001", "status": "settled", "settled_at": "2026-01-02"},
    ])
    result = check_missing_settlement(sample_payments, settlements)
    # pay_2 and pay_3 are captured but not settled
    assert len(result) == 2
    types = [a["type"] for a in result]
    assert all(t == "missing_settlement" for t in types)


def test_orphan_records(sample_payments):
    orders = pd.DataFrame([
        {"order_id": "ord_1", "amount": 1000.00, "currency": "INR", "status": "paid", "created_at": "2026-01-01"},
    ])
    refunds = pd.DataFrame([
        {"refund_id": "rfnd_orphan", "payment_id": "pay_999", "order_id": "ord_999", "amount": 100.00, "status": "processed", "created_at": "2026-01-01"},
    ])
    result = check_orphan_records(sample_payments, refunds, orders)
    # pay_2, pay_3 reference non-existent orders; rfnd_orphan references non-existent payment
    assert len(result) >= 1
    types = [a["type"] for a in result]
    assert all(t == "orphan_record" for t in types)
