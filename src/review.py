"""
Human Review Queue

Manages investigations that need human review (confidence below threshold).
"""
from config import CONFIDENCE_REVIEW_THRESHOLD


def get_review_queue(investigations: list[dict]) -> list[dict]:
    """Return investigations that need human review."""
    return [inv for inv in investigations if inv["confidence"] < CONFIDENCE_REVIEW_THRESHOLD]


def accept_investigation(investigation: dict, reviewer: str = "analyst", comment: str = "") -> dict:
    """Mark an investigation as accepted."""
    investigation["status"] = "accepted"
    investigation["review"] = {
        "action": "accepted",
        "reviewer": reviewer,
        "comment": comment,
    }
    return investigation


def reject_investigation(investigation: dict, reviewer: str = "analyst", comment: str = "") -> dict:
    """Mark an investigation as rejected (false positive)."""
    investigation["status"] = "rejected"
    investigation["review"] = {
        "action": "rejected",
        "reviewer": reviewer,
        "comment": comment,
    }
    return investigation
