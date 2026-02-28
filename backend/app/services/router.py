"""Confidence-gated routing: auto-post / review / manual."""

from app.config import CONFIDENCE_AUTO_POST, CONFIDENCE_REVIEW


def route_prediction(confidence_score: float) -> tuple[str, str]:
    """
    Determine routing action based on confidence score.

    Returns:
        (status, routed_action) tuple
    """
    if confidence_score >= CONFIDENCE_AUTO_POST:
        return "auto_posted", "auto_post_to_erp"
    elif confidence_score >= CONFIDENCE_REVIEW:
        return "pending_review", "human_review"
    else:
        return "manual_required", "manual_classification"
