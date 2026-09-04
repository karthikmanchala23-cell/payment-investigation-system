"""
Tests for Data Loader & Validator
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from io import StringIO

from src.data_loader import validate_dataframe, load_csvs


def test_valid_orders():
    df = pd.DataFrame([
        {"order_id": "ord_1", "amount": 1000, "currency": "INR", "status": "paid", "created_at": "2026-01-01"},
    ])
    errors = validate_dataframe(df, "orders")
    assert errors == []


def test_missing_columns():
    df = pd.DataFrame([{"order_id": "ord_1", "amount": 1000}])
    errors = validate_dataframe(df, "orders")
    assert len(errors) == 1
    assert "missing columns" in errors[0]


def test_empty_dataframe():
    df = pd.DataFrame(columns=["order_id", "amount", "currency", "status", "created_at"])
    errors = validate_dataframe(df, "orders")
    assert any("empty" in e for e in errors)


def test_unknown_data_type():
    df = pd.DataFrame([{"x": 1}])
    errors = validate_dataframe(df, "unknown_table")
    assert any("Unknown" in e for e in errors)


def test_load_csvs_from_buffers():
    csv_data = "order_id,amount,currency,status,created_at\nord_1,1000,INR,paid,2026-01-01\n"
    data, errors = load_csvs({"orders": StringIO(csv_data)})
    assert errors == []
    assert "orders" in data
    assert len(data["orders"]) == 1
