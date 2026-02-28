"""Mock ERP posting endpoint, dashboard stats, and retrain trigger."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    Transaction, Prediction, Correction, AuditLog, ERPPosting
)
from app.schemas import DashboardStats, RetrainResponse
from app.services.erp_client import post_to_erp
from app.services.retrainer import retrain_from_corrections
from app.ml.vector_store import get_total_vectors

router = APIRouter(prefix="/api", tags=["ERP & Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get summary statistics for the dashboard."""
    total_txn = db.query(func.count(Transaction.id)).scalar() or 0
    total_pred = db.query(func.count(Prediction.id)).scalar() or 0
    auto_posted = db.query(func.count(Prediction.id)).filter(Prediction.status == "auto_posted").scalar() or 0
    pending_review = db.query(func.count(Prediction.id)).filter(Prediction.status == "pending_review").scalar() or 0
    manual_required = db.query(func.count(Prediction.id)).filter(Prediction.status == "manual_required").scalar() or 0
    approved = db.query(func.count(Prediction.id)).filter(Prediction.status == "approved").scalar() or 0
    rejected = db.query(func.count(Prediction.id)).filter(Prediction.status == "rejected").scalar() or 0
    avg_conf = db.query(func.avg(Prediction.confidence_score)).scalar() or 0.0
    total_corrections = db.query(func.count(Correction.id)).scalar() or 0
    correction_rate = (total_corrections / total_pred * 100) if total_pred > 0 else 0.0
    total_erp = db.query(func.count(ERPPosting.id)).scalar() or 0

    return DashboardStats(
        total_transactions=total_txn,
        total_predictions=total_pred,
        auto_posted_count=auto_posted,
        pending_review_count=pending_review,
        manual_required_count=manual_required,
        approved_count=approved,
        rejected_count=rejected,
        avg_confidence=round(avg_conf, 2),
        correction_rate=round(correction_rate, 2),
        total_erp_postings=total_erp,
    )


@router.post("/ml/retrain", response_model=RetrainResponse)
def trigger_retrain(db: Session = Depends(get_db)):
    """Manually trigger retraining from accumulated corrections."""
    result = retrain_from_corrections(db)
    return RetrainResponse(
        message=result["message"],
        corrections_used=result["corrections_used"],
        new_vectors_added=result["new_vectors_added"],
    )


@router.get("/ml/status")
def ml_status():
    """Get ML model / vector store status."""
    return {
        "total_vectors": get_total_vectors(),
        "model": "all-MiniLM-L6-v2",
        "embedding_dimension": 384,
    }
