"""Prediction and classification endpoints."""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction, Transaction
from app.schemas import PredictionRead, ClassifyRequest, ClassifyResponse, CandidateGL
from app.services.classifier import classify_batch

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.post("/classify", response_model=ClassifyResponse)
def classify_transactions(
    request: ClassifyRequest,
    db: Session = Depends(get_db),
):
    """Classify unclassified transactions and route based on confidence."""
    result = classify_batch(
        db,
        transaction_ids=request.transaction_ids,
        batch_id=request.batch_id,
    )
    return ClassifyResponse(**result)


@router.get("", response_model=list[PredictionRead])
def list_predictions(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    min_confidence: float | None = None,
    max_confidence: float | None = None,
    db: Session = Depends(get_db),
):
    """List predictions with optional filters."""
    query = db.query(Prediction)

    if status:
        query = query.filter(Prediction.status == status)
    if min_confidence is not None:
        query = query.filter(Prediction.confidence_score >= min_confidence)
    if max_confidence is not None:
        query = query.filter(Prediction.confidence_score <= max_confidence)

    predictions = query.order_by(Prediction.id.desc()).offset(skip).limit(limit).all()

    # Parse top_candidates JSON and attach transaction data
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
