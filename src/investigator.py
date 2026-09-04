"""
Investigation Grouper — Key Differentiator

Groups related anomalies into investigations using graph-based entity linking.
Multiple symptoms sharing transaction/payment/order/refund/settlement/batch IDs
are merged into a single investigation with a deterministic root-cause category.
"""
from collections import defaultdict

from config import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW


# --- Root-cause inference rules ---
ROOT_CAUSE_RULES = [
    {
        "pattern": {"settlement_mismatch", "duplicate_settlement"},
        "cause": "Settlement pipeline double-processing",
    },
    {
        "pattern": {"missing_payment", "orphan_record"},
        "cause": "Order processing failure",
    },
    {
        "pattern": {"payment_order_mismatch", "incorrect_refund_amount"},
        "cause": "Amount propagation error",
    },
    {
        "pattern": {"missing_settlement", "settlement_mismatch"},
        "cause": "Settlement pipeline error",
    },
    {
        "pattern": {"duplicate_payment", "settlement_mismatch"},
        "cause": "Duplicate charge with settlement impact",
    },
    {
        "pattern": {"missing_refund", "incorrect_refund_amount"},
        "cause": "Refund processing failure",
    },
]

SEVERITY_RANK = {SEVERITY_CRITICAL: 4, SEVERITY_HIGH: 3, SEVERITY_MEDIUM: 2, SEVERITY_LOW: 1}
PRIORITY_MAP = {4: "critical", 3: "high", 2: "medium", 1: "low"}


def _extract_entity_ids(anomaly: dict) -> set:
    """Extract all entity IDs from an anomaly for graph linking."""
    ids = set()
    for rid in anomaly.get("record_ids", []):
        ids.add(rid)
    # Also extract batch_id if present in evidence
    evidence = anomaly.get("evidence", {})
    for key in ("batch_id", "batches"):
        if key in evidence:
            val = evidence[key]
            if isinstance(val, list):
                ids.update(val)
            else:
                ids.add(val)
    return ids


def _find_connected_components(anomalies: list[dict]) -> list[list[int]]:
    """
    Build a graph where anomalies are nodes and edges connect anomalies
    sharing any entity ID. Return connected components as lists of indices.
    """
    n = len(anomalies)
    if n == 0:
        return []

    # Map entity ID → list of anomaly indices
    entity_to_anomalies = defaultdict(set)
    for i, a in enumerate(anomalies):
        for eid in _extract_entity_ids(a):
            entity_to_anomalies[eid].add(i)

    # Union-Find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Connect anomalies sharing entity IDs
    for indices in entity_to_anomalies.values():
        idx_list = list(indices)
        for i in range(1, len(idx_list)):
            union(idx_list[0], idx_list[i])

    # Group by component
    components = defaultdict(list)
    for i in range(n):
        components[find(i)].append(i)

    return list(components.values())


def _infer_root_cause(anomaly_types: set) -> tuple[str, float]:
    """
    Infer a root cause category from the mix of anomaly types.
    Returns (root_cause_string, confidence).
    """
    # Check multi-type rules first
    for rule in ROOT_CAUSE_RULES:
        if rule["pattern"].issubset(anomaly_types):
            return rule["cause"], 0.85

    # Single-type fallback
    type_to_cause = {
        "payment_order_mismatch": "Payment amount discrepancy",
        "missing_payment": "Missing payment record",
        "duplicate_payment": "Duplicate payment processing",
        "missing_refund": "Refund not processed",
        "incorrect_refund_amount": "Refund amount error",
        "settlement_mismatch": "Settlement amount discrepancy",
        "duplicate_settlement": "Duplicate settlement entry",
        "missing_settlement": "Settlement not recorded",
        "orphan_record": "Orphan/incomplete record",
    }

    if len(anomaly_types) == 1:
        t = next(iter(anomaly_types))
        return type_to_cause.get(t, "Unknown"), 0.90

    # Multiple unrelated types
    causes = [type_to_cause.get(t, t) for t in anomaly_types]
    return f"Multiple issues: {', '.join(causes)}", 0.65


def _compute_priority(anomalies: list[dict]) -> str:
    """Compute priority from max severity of constituent anomalies."""
    max_rank = max(SEVERITY_RANK.get(a["severity"], 1) for a in anomalies)
    # Bump priority if many anomalies
    if len(anomalies) >= 3 and max_rank < 4:
        max_rank = min(max_rank + 1, 4)
    return PRIORITY_MAP.get(max_rank, "medium")


def group_into_investigations(anomalies: list[dict]) -> list[dict]:
    """
    Group anomalies into investigations using graph-based entity linking.

    Returns list of Investigation dicts, each containing:
        - id, title, anomalies, anomaly_types, root_cause, confidence,
          priority, record_ids, total_amount_affected
    """
    if not anomalies:
        return []

    components = _find_connected_components(anomalies)
    investigations = []

    for inv_idx, component_indices in enumerate(components):
        inv_anomalies = [anomalies[i] for i in component_indices]
        anomaly_types = {a["type"] for a in inv_anomalies}
        all_record_ids = set()
        for a in inv_anomalies:
            all_record_ids.update(a.get("record_ids", []))

        root_cause, confidence = _infer_root_cause(anomaly_types)
        priority = _compute_priority(inv_anomalies)

        # Estimate total amount affected from evidence
        total_amount = 0.0
        for a in inv_anomalies:
            ev = a.get("evidence", {})
            for key in ("payment_amount", "order_amount", "refund_amount", "settlement_amount"):
                if key in ev:
                    total_amount += ev[key]
                    break  # count one amount per anomaly

        investigations.append({
            "id": f"INV-{inv_idx + 1:04d}",
            "title": root_cause,
            "anomalies": inv_anomalies,
            "anomaly_types": list(anomaly_types),
            "root_cause": root_cause,
            "confidence": round(confidence, 2),
            "priority": priority,
            "record_ids": list(all_record_ids),
            "total_amount_affected": round(total_amount, 2),
            "status": "open",
            "ai_analysis": None,  # filled by Gemini later
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    investigations.sort(key=lambda inv: priority_order.get(inv["priority"], 99))

    return investigations
