"""
Audit Trail

Append-only log of all actions taken on investigations.
"""
from datetime import datetime


def create_audit_log() -> list[dict]:
    """Create an empty audit log."""
    return []


def log_action(audit_log: list, action: str, investigation_id: str,
               user: str = "system", details: str = "") -> list:
    """Append an action to the audit log."""
    audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "investigation_id": investigation_id,
        "user": user,
        "details": details,
    })
    return audit_log


def log_analysis_run(audit_log: list, num_anomalies: int, num_investigations: int) -> list:
    """Log an analysis run event."""
    return log_action(
        audit_log, "analysis_run", "ALL",
        details=f"Detected {num_anomalies} anomalies in {num_investigations} investigations",
    )


def log_review(audit_log: list, investigation_id: str, action: str,
               reviewer: str, comment: str = "") -> list:
    """Log a review action (accept/reject)."""
    return log_action(
        audit_log, f"review_{action}", investigation_id,
        user=reviewer, details=comment,
    )
