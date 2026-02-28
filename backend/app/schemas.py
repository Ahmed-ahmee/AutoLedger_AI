"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ── Chart of Accounts ──────────────────────────────────────────────────
class COABase(BaseModel):
    gl_code: str
    gl_name: str
    category: str
    sub_category: Optional[str] = None

class COARead(COABase):
    id: int
    class Config:
        from_attributes = True


# ── Transactions ───────────────────────────────────────────────────────
class TransactionBase(BaseModel):
    transaction_date: Optional[datetime] = None
    description: str
    amount: float = 0.0
    vendor: Optional[str] = None
    department: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionRead(TransactionBase):
    id: int
    batch_id: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class TransactionUploadResponse(BaseModel):
    batch_id: str
    total_transactions: int
    message: str


# ── Predictions ────────────────────────────────────────────────────────
class CandidateGL(BaseModel):
    gl_code: str
    gl_name: str
    score: float

class PredictionRead(BaseModel):
    id: int
    transaction_id: int
    predicted_gl_code: str
    predicted_gl_name: Optional[str] = None
    confidence_score: float
    status: str
    routed_action: Optional[str] = None
    top_candidates: Optional[List[CandidateGL]] = None
    created_at: datetime
    transaction: Optional[TransactionRead] = None
    class Config:
        from_attributes = True

class ClassifyRequest(BaseModel):
    transaction_ids: Optional[List[int]] = None  # None = classify all unclassified
    batch_id: Optional[str] = None

class ClassifyResponse(BaseModel):
    total_classified: int
    auto_posted: int
    pending_review: int
    manual_required: int


# ── Reviews ────────────────────────────────────────────────────────────
class ReviewAction(BaseModel):
    corrected_gl_code: Optional[str] = None
    reason: Optional[str] = None
    corrected_by: Optional[str] = "analyst"


# ── Corrections ────────────────────────────────────────────────────────
class CorrectionRead(BaseModel):
    id: int
    prediction_id: int
    original_gl_code: str
    corrected_gl_code: str
    corrected_by: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ── Audit Logs ─────────────────────────────────────────────────────────
class AuditLogRead(BaseModel):
    id: int
    transaction_id: Optional[int] = None
    action: str
    actor: str
    details: Optional[str] = None
    timestamp: datetime
    class Config:
        from_attributes = True


# ── ERP Postings ───────────────────────────────────────────────────────
class ERPPostingRead(BaseModel):
    id: int
    transaction_id: int
    gl_code: str
    amount: float
    erp_response_code: Optional[str] = None
    erp_response_message: Optional[str] = None
    posted_at: datetime
    class Config:
        from_attributes = True

class ERPPostResponse(BaseModel):
    success: bool
    erp_response_code: str
    erp_response_message: str
    posting_id: Optional[int] = None


# ── Dashboard Stats ───────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_transactions: int
    total_predictions: int
    auto_posted_count: int
    pending_review_count: int
    manual_required_count: int
    approved_count: int
    rejected_count: int
    avg_confidence: float
    correction_rate: float
    total_erp_postings: int


# ── Retrain ────────────────────────────────────────────────────────────
class RetrainResponse(BaseModel):
    message: str
    corrections_used: int
    new_vectors_added: int
