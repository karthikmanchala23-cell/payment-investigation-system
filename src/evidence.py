"""
Evidence Chain Builder

Collects the exact source records that support each finding in an investigation.
"""
from datetime import datetime

import pandas as pd


def build_evidence_chain(investigation: dict, data: dict[str, pd.DataFrame]) -> list[dict]:
    """
    For an investigation, gather all supporting source records.

    Returns a list of Evidence dicts:
        {finding, check_name, supporting_records, timestamp}
    """
    evidence_chain = []
    record_ids = set(investigation.get("record_ids", []))

    for anomaly in investigation["anomalies"]:
        supporting = []

        for rid in anomaly.get("record_ids", []):
            # Search across all data tables for this record
            for table_name, df in data.items():
                id_cols = [c for c in df.columns if c.endswith("_id")]
                for col in id_cols:
                    matches = df[df[col] == rid]
                    if not matches.empty:
                        for _, row in matches.iterrows():
                            supporting.append({
                                "source_table": table_name,
                                "record_id": rid,
                                "id_column": col,
                                "record": row.to_dict(),
                            })

        evidence_chain.append({
            "finding": anomaly["details"],
            "check_name": anomaly["type"],
            "severity": anomaly["severity"],
            "supporting_records": supporting,
            "timestamp": datetime.now().isoformat(),
        })

    return evidence_chain


def build_all_evidence(investigations: list[dict], data: dict[str, pd.DataFrame]) -> dict[str, list[dict]]:
    """Build evidence chains for all investigations. Returns {inv_id: evidence_chain}."""
    evidence_map = {}
    for inv in investigations:
        evidence_map[inv["id"]] = build_evidence_chain(inv, data)
    return evidence_map
