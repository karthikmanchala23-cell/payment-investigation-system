"""
Tests for Ground-Truth Evaluator
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.evaluator import evaluate


def test_perfect_detection():
    """All ground truth anomalies detected, nothing extra."""
    detected = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "test"},
        {"type": "duplicate_payment", "record_ids": ["ord_2", "pay_2", "pay_3"], "details": "test"},
    ]
    ground_truth = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "test"},
        {"type": "duplicate_payment", "record_ids": ["ord_2", "pay_2", "pay_3"], "details": "test"},
    ]
    result = evaluate(detected, ground_truth)
    assert result["overall"]["precision"] == 1.0
    assert result["overall"]["recall"] == 1.0
    assert result["overall"]["f1"] == 1.0


def test_false_positive():
    """Detected something not in ground truth."""
    detected = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "test"},
        {"type": "orphan_record", "record_ids": ["rfnd_99"], "details": "extra"},
    ]
    ground_truth = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "test"},
    ]
    result = evaluate(detected, ground_truth)
    assert result["overall"]["precision"] == 0.5
    assert result["overall"]["recall"] == 1.0


def test_false_negative():
    """Missed something in ground truth."""
    detected = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "test"},
    ]
    ground_truth = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "test"},
        {"type": "duplicate_payment", "record_ids": ["ord_2", "pay_2"], "details": "missed"},
    ]
    result = evaluate(detected, ground_truth)
    assert result["overall"]["precision"] == 1.0
    assert result["overall"]["recall"] == 0.5


def test_empty_inputs():
    """Both empty → zero metrics."""
    result = evaluate([], [])
    assert result["overall"]["precision"] == 0.0
    assert result["overall"]["recall"] == 0.0


def test_per_type_metrics():
    """Per-type breakdown should be computed."""
    detected = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "a"},
        {"type": "settlement_mismatch", "record_ids": ["stl_1", "pay_1"], "details": "b"},
    ]
    ground_truth = [
        {"type": "missing_payment", "record_ids": ["ord_1"], "details": "a"},
    ]
    result = evaluate(detected, ground_truth)
    assert "missing_payment" in result["per_type"]
    assert result["per_type"]["missing_payment"]["precision"] == 1.0
