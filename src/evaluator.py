"""
Ground-Truth Evaluator

Compares detected anomalies against known ground truth to compute
precision, recall, and F1 per anomaly type and overall.
"""
import json
from collections import defaultdict


def load_ground_truth(path: str = "data/ground_truth.json") -> list[dict]:
    """Load ground truth from JSON file."""
    with open(path) as f:
        return json.load(f)


def _anomaly_key(anomaly: dict) -> str:
    """Create a unique key for matching: type + sorted record IDs."""
    ids = sorted(anomaly.get("record_ids", []))
    return f"{anomaly['type']}|{'|'.join(ids)}"


def evaluate(detected: list[dict], ground_truth: list[dict]) -> dict:
    """
    Compare detected anomalies against ground truth.

    Returns:
        dict with 'overall' and 'per_type' metrics, plus
        'false_positives' and 'false_negatives' lists.
    """
    # Build key sets
    detected_keys = {_anomaly_key(a) for a in detected}
    truth_keys = {_anomaly_key(a) for a in ground_truth}

    # Also match by type + any overlapping record ID (looser match)
    def _loose_match(det_set, truth_set, det_list, truth_list):
        tp, fp_list, fn_list = 0, [], []
        matched_truth = set()

        for d in det_list:
            d_ids = set(d.get("record_ids", []))
            found = False
            for i, t in enumerate(truth_list):
                if i in matched_truth:
                    continue
                if d["type"] == t["type"] and d_ids & set(t.get("record_ids", [])):
                    tp += 1
                    matched_truth.add(i)
                    found = True
                    break
            if not found:
                fp_list.append(d)

        for i, t in enumerate(truth_list):
            if i not in matched_truth:
                fn_list.append(t)

        return tp, fp_list, fn_list

    tp, false_positives, false_negatives = _loose_match(
        detected_keys, truth_keys, detected, ground_truth
    )

    precision = tp / (tp + len(false_positives)) if (tp + len(false_positives)) > 0 else 0.0
    recall = tp / (tp + len(false_negatives)) if (tp + len(false_negatives)) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Per-type metrics
    per_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for d in detected:
        d_ids = set(d.get("record_ids", []))
        matched = False
        for t in ground_truth:
            if d["type"] == t["type"] and d_ids & set(t.get("record_ids", [])):
                matched = True
                break
        if matched:
            per_type[d["type"]]["tp"] += 1
        else:
            per_type[d["type"]]["fp"] += 1

    for t in false_negatives:
        per_type[t["type"]]["fn"] += 1

    per_type_metrics = {}
    for atype, counts in per_type.items():
        p = counts["tp"] / (counts["tp"] + counts["fp"]) if (counts["tp"] + counts["fp"]) > 0 else 0.0
        r = counts["tp"] / (counts["tp"] + counts["fn"]) if (counts["tp"] + counts["fn"]) > 0 else 0.0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        per_type_metrics[atype] = {
            "precision": round(p, 3),
            "recall": round(r, 3),
            "f1": round(f, 3),
            "true_positives": counts["tp"],
            "false_positives": counts["fp"],
            "false_negatives": counts["fn"],
        }

    return {
        "overall": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "true_positives": tp,
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "total_detected": len(detected),
            "total_ground_truth": len(ground_truth),
        },
        "per_type": per_type_metrics,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }
