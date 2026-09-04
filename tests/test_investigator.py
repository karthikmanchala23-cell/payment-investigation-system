"""
Tests for Investigation Grouper
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.investigator import group_into_investigations


def test_separate_anomalies_stay_separate():
    """Anomalies with no shared IDs should create separate investigations."""
    anomalies = [
        {"type": "missing_payment", "severity": "critical", "record_ids": ["ord_1"], "details": "test", "evidence": {}},
        {"type": "missing_payment", "severity": "critical", "record_ids": ["ord_2"], "details": "test", "evidence": {}},
    ]
    investigations = group_into_investigations(anomalies)
    assert len(investigations) == 2


def test_overlapping_ids_merge():
    """Anomalies sharing a record ID should merge into one investigation."""
    anomalies = [
        {"type": "payment_order_mismatch", "severity": "high", "record_ids": ["ord_1", "pay_1"], "details": "test", "evidence": {}},
        {"type": "missing_settlement", "severity": "high", "record_ids": ["pay_1"], "details": "test", "evidence": {}},
    ]
    investigations = group_into_investigations(anomalies)
    assert len(investigations) == 1
    assert len(investigations[0]["anomalies"]) == 2


def test_transitive_merge():
    """A-B and B-C should merge into one investigation (transitive)."""
    anomalies = [
        {"type": "payment_order_mismatch", "severity": "high", "record_ids": ["ord_1", "pay_1"], "details": "test", "evidence": {}},
        {"type": "settlement_mismatch", "severity": "high", "record_ids": ["pay_1", "stl_1"], "details": "test", "evidence": {}},
        {"type": "duplicate_settlement", "severity": "critical", "record_ids": ["stl_1", "stl_2"], "details": "test", "evidence": {}},
    ]
    investigations = group_into_investigations(anomalies)
    assert len(investigations) == 1
    assert len(investigations[0]["anomalies"]) == 3


def test_root_cause_inference_single_type():
    """Single anomaly type should give direct root cause."""
    anomalies = [
        {"type": "duplicate_payment", "severity": "high", "record_ids": ["ord_1", "pay_1", "pay_2"], "details": "test", "evidence": {}},
    ]
    investigations = group_into_investigations(anomalies)
    assert investigations[0]["root_cause"] == "Duplicate payment processing"


def test_root_cause_inference_multi_type():
    """Known pattern should trigger the matching root cause rule."""
    anomalies = [
        {"type": "settlement_mismatch", "severity": "high", "record_ids": ["pay_1", "stl_1"], "details": "test", "evidence": {}},
        {"type": "duplicate_settlement", "severity": "critical", "record_ids": ["pay_1", "stl_1", "stl_2"], "details": "test", "evidence": {}},
    ]
    investigations = group_into_investigations(anomalies)
    assert investigations[0]["root_cause"] == "Settlement pipeline double-processing"


def test_priority_escalation():
    """Priority should escalate when 3+ anomalies are grouped."""
    anomalies = [
        {"type": "missing_payment", "severity": "medium", "record_ids": ["ord_1"], "details": "test", "evidence": {}},
        {"type": "orphan_record", "severity": "medium", "record_ids": ["ord_1", "rfnd_1"], "details": "test", "evidence": {}},
        {"type": "missing_settlement", "severity": "medium", "record_ids": ["ord_1", "pay_1"], "details": "test", "evidence": {}},
    ]
    investigations = group_into_investigations(anomalies)
    assert len(investigations) == 1
    assert investigations[0]["priority"] in ("high", "critical")


def test_empty_anomalies():
    """Empty input should return empty output."""
    assert group_into_investigations([]) == []
