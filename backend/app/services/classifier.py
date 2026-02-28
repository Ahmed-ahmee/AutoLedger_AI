"""
Classification service – orchestrates ML pipeline for single/batch transactions.
"""

import json
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Transaction, Prediction, AuditLog
from app.ml.pipeline import classify_transaction
from app.services.router import route_prediction
from app.services.erp_client import post_to_erp
from app.models import ERPPosting


def classify_and_route(db: Session, transaction: Transaction) -> Prediction:
    """
    Classify a single transaction and route based on confidence.

    Steps:
      1. Run ML prediction
      2. Determine routing action
      3. If auto-post, call mock ERP
      4. Save prediction + audit log
    """
    # 1. ML prediction
    result = classify_transaction(
        description=transaction.description,
        vendor=transaction.vendor or "",
        department=transaction.department or "",
    )

    # 2. Route based on confidence
    status, routed_action = route_prediction(result["confidence_score"])

    # 3. Create prediction record
    prediction = Prediction(
        transaction_id=transaction.id,
        predicted_gl_code=result["predicted_gl_code"],
        predicted_gl_name=result["predicted_gl_name"],
        confidence_score=result["confidence_score"],
        status=status,
        routed_action=routed_action,
        top_candidates=json.dumps(result["top_candidates"]),
        created_at=datetime.utcnow(),
    )
    db.add(prediction)

    # 4. Audit log – prediction
    audit = AuditLog(
        transaction_id=transaction.id,
        action="predicted",
        actor="system",
        details=f"GL: {result['predicted_gl_code']}, Confidence: {result['confidence_score']}%, Route: {routed_action}",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)

    # 5. If auto-post, call ERP
    if status == "auto_posted":
        erp_result = post_to_erp(
            transaction_id=transaction.id,
            gl_code=result["predicted_gl_code"],
            amount=transaction.amount,
            description=transaction.description,
        )

        erp_posting = ERPPosting(
            transaction_id=transaction.id,
            gl_code=result["predicted_gl_code"],
            amount=transaction.amount,
            erp_response_code=erp_result["erp_response_code"],
            erp_response_message=erp_result["erp_response_message"],
            posted_at=datetime.utcnow(),
        )
        db.add(erp_posting)

        # Audit log – ERP posting
        erp_audit = AuditLog(
            transaction_id=transaction.id,
            action="auto_posted",
            actor="system",
            details=f"ERP response: {erp_result['erp_response_code']} – {erp_result['erp_response_message']}",
            timestamp=datetime.utcnow(),
        )
        db.add(erp_audit)

    elif status == "pending_review":
        # Audit log – sent for review
        review_audit = AuditLog(
            transaction_id=transaction.id,
            action="sent_for_review",
            actor="system",
            details=f"Confidence {result['confidence_score']}% – routed to human review",
            timestamp=datetime.utcnow(),
        )
        db.add(review_audit)

    db.commit()
    db.refresh(prediction)
    return prediction


def classify_batch(
    db: Session,
    transaction_ids: list[int] | None = None,
    batch_id: str | None = None,
) -> dict:
    """
    Classify a batch of transactions.

    Returns summary counts.
    """
    query = db.query(Transaction)

    if transaction_ids:
        query = query.filter(Transaction.id.in_(transaction_ids))
    elif batch_id:
        query = query.filter(Transaction.batch_id == batch_id)

    # Only classify transactions without predictions
    classified_ids = (
        db.query(Prediction.transaction_id)
        .subquery()
    )
    transactions = query.filter(~Transaction.id.in_(classified_ids)).all()

    counts = {"auto_posted": 0, "pending_review": 0, "manual_required": 0}

    for txn in transactions:
        prediction = classify_and_route(db, txn)
        counts[prediction.status] = counts.get(prediction.status, 0) + 1

    return {
        "total_classified": len(transactions),
        **counts,
    }
