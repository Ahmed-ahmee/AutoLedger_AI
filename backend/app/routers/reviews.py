"""Human review queue endpoints – approve / reject with corrections."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction, Correction, Transaction, ERPPosting
from app.schemas import PredictionRead, ReviewAction, CandidateGL
from app.services.erp_client import post_to_erp
from app.utils.audit_logger import log_audit

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.get("/queue", response_model=list[PredictionRead])
def get_review_queue(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get all predictions pending human review."""
    predictions = (
        db.query(Prediction)
        .filter(Prediction.status.in_(["pending_review", "manual_required"]))
        .order_by(Prediction.confidence_score.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for pred in predictions:
        txn = db.query(Transaction).get(pred.transaction_id)
        candidates = []
        if pred.top_candidates:
            try:
                candidates = [CandidateGL(**c) for c in json.loads(pred.top_candidates)]
            except (json.JSONDecodeError, TypeError):
                pass

        result.append(PredictionRead(
            id=pred.id,
            transaction_id=pred.transaction_id,
            predicted_gl_code=pred.predicted_gl_code,
            predicted_gl_name=pred.predicted_gl_name,
            confidence_score=pred.confidence_score,
            status=pred.status,
            routed_action=pred.routed_action,
            top_candidates=candidates,
            created_at=pred.created_at,
            transaction=txn,
        ))

    return result


@router.post("/{prediction_id}/approve")
def approve_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """Approve a prediction – post to ERP."""
    prediction = db.query(Prediction).get(prediction_id)
    if not prediction:
        raise HTTPException(404, "Prediction not found")
    if prediction.status not in ("pending_review", "manual_required"):
        raise HTTPException(400, f"Cannot approve prediction with status '{prediction.status}'")

    transaction = db.query(Transaction).get(prediction.transaction_id)

    # Update status
    prediction.status = "approved"
    db.commit()

    # Post to mock ERP
    erp_result = post_to_erp(
        transaction_id=transaction.id,
        gl_code=prediction.predicted_gl_code,
        amount=transaction.amount,
        description=transaction.description,
    )

    erp_posting = ERPPosting(
        transaction_id=transaction.id,
        gl_code=prediction.predicted_gl_code,
        amount=transaction.amount,
        erp_response_code=erp_result["erp_response_code"],
        erp_response_message=erp_result["erp_response_message"],
        posted_at=datetime.utcnow(),
    )
    db.add(erp_posting)

    # Audit
    log_audit(
        db, action="approved", actor="analyst",
        transaction_id=transaction.id,
        details=f"Approved GL: {prediction.predicted_gl_code}. ERP: {erp_result['erp_response_code']}"
    )

    return {"message": "Prediction approved and posted to ERP", "erp_result": erp_result}


@router.post("/{prediction_id}/reject")
def reject_prediction(
    prediction_id: int,
    review: ReviewAction,
    db: Session = Depends(get_db),
):
    """Reject a prediction and provide correction."""
    prediction = db.query(Prediction).get(prediction_id)
    if not prediction:
        raise HTTPException(404, "Prediction not found")
    if prediction.status not in ("pending_review", "manual_required"):
        raise HTTPException(400, f"Cannot reject prediction with status '{prediction.status}'")
    if not review.corrected_gl_code:
        raise HTTPException(400, "corrected_gl_code is required for rejection")

    transaction = db.query(Transaction).get(prediction.transaction_id)

    # Update status
    prediction.status = "rejected"
    db.commit()

    # Create correction record
    correction = Correction(
        prediction_id=prediction.id,
        original_gl_code=prediction.predicted_gl_code,
        corrected_gl_code=review.corrected_gl_code,
        corrected_by=review.corrected_by or "analyst",
        reason=review.reason,
        created_at=datetime.utcnow(),
    )
    db.add(correction)

    # Post corrected entry to ERP
    erp_result = post_to_erp(
        transaction_id=transaction.id,
        gl_code=review.corrected_gl_code,
        amount=transaction.amount,
        description=transaction.description,
    )

    erp_posting = ERPPosting(
        transaction_id=transaction.id,
        gl_code=review.corrected_gl_code,
        amount=transaction.amount,
        erp_response_code=erp_result["erp_response_code"],
        erp_response_message=erp_result["erp_response_message"],
        posted_at=datetime.utcnow(),
    )
    db.add(erp_posting)

    # Audit
    log_audit(
        db, action="rejected", actor=review.corrected_by or "analyst",
        transaction_id=transaction.id,
        details=f"Rejected GL: {prediction.predicted_gl_code} → Corrected to: {review.corrected_gl_code}. Reason: {review.reason or 'N/A'}"
    )

    return {
        "message": "Prediction rejected, correction saved, and corrected entry posted to ERP",
        "correction_id": correction.id,
        "erp_result": erp_result,
    }
