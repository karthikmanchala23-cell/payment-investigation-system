"""
Gemini AI Analyzer — Advisory Only

Gemini NEVER overrides deterministic financial facts.
It receives evidence as read-only input and produces only:
1. Root-cause hypothesis
2. Plain-language explanation
3. Recommended next step
"""
import json
import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL

_model = None


def _get_model():
    """Lazy-init Gemini model."""
    global _model
    if _model is None and GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel(GEMINI_MODEL)
    return _model


SYSTEM_PROMPT = """You are a payment investigation analyst AI assistant.
You will receive an investigation containing deterministic anomaly findings and evidence.

IMPORTANT RULES:
- You must NEVER override, modify, or contradict the deterministic findings.
- The anomalies and evidence are verified financial facts — treat them as ground truth.
- Your role is ADVISORY ONLY: provide insight, not corrections to the findings.

Based on the evidence provided, respond with a JSON object containing exactly:
{
  "root_cause_hypothesis": "Your best hypothesis for why these anomalies occurred",
  "explanation": "A clear, plain-language explanation suitable for a non-technical reviewer",
  "recommended_action": "What a human investigator should do next"
}

Keep each field to 2-3 sentences maximum. Be specific and actionable."""


def analyze_investigation(investigation: dict) -> dict | None:
    """
    Send investigation evidence to Gemini for advisory analysis.

    Returns dict with root_cause_hypothesis, explanation, recommended_action
    or None if API unavailable.
    """
    model = _get_model()
    if model is None:
        return None

    # Build a concise prompt with just the facts
    prompt_data = {
        "investigation_id": investigation["id"],
        "deterministic_root_cause": investigation["root_cause"],
        "priority": investigation["priority"],
        "confidence": investigation["confidence"],
        "anomaly_count": len(investigation["anomalies"]),
        "anomaly_types": investigation["anomaly_types"],
        "total_amount_affected": investigation["total_amount_affected"],
        "anomaly_details": [
            {"type": a["type"], "severity": a["severity"], "details": a["details"]}
            for a in investigation["anomalies"]
        ],
    }

    prompt = f"{SYSTEM_PROMPT}\n\nInvestigation data:\n{json.dumps(prompt_data, indent=2)}"

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Try to parse JSON from the response
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        return {
            "root_cause_hypothesis": result.get("root_cause_hypothesis", ""),
            "explanation": result.get("explanation", ""),
            "recommended_action": result.get("recommended_action", ""),
        }
    except Exception:
        return None


def get_fallback_analysis(investigation: dict) -> dict:
    """Deterministic fallback when Gemini is unavailable."""
    anomaly_details = "; ".join(a["details"] for a in investigation["anomalies"][:3])
    return {
        "root_cause_hypothesis": investigation["root_cause"],
        "explanation": f"This investigation contains {len(investigation['anomalies'])} anomaly(ies): {anomaly_details}",
        "recommended_action": f"Review the {len(investigation['anomalies'])} flagged records and verify amounts against source systems.",
    }


def enrich_investigations(investigations: list[dict]) -> list[dict]:
    """Add AI analysis to each investigation, with fallback."""
    for inv in investigations:
        ai_result = analyze_investigation(inv)
        if ai_result is None:
            ai_result = get_fallback_analysis(inv)
        inv["ai_analysis"] = ai_result
    return investigations
