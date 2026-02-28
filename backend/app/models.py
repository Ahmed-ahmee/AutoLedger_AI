"""SQLAlchemy ORM models for AutoLedger AI."""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"

    id = Column(Integer, primary_key=True, index=True)
    gl_code = Column(String(10), unique=True, nullable=False, index=True)
    gl_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)       # Assets, Liabilities, etc.
    sub_category = Column(String(100), nullable=True)    # Cash & Bank, etc.

    def __repr__(self):
        return f"<COA {self.gl_code} – {self.gl_name}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=True, index=True)
    transaction_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    vendor = Column(String(200), nullable=True)
    department = Column(String(100), nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="transaction")
    audit_logs = relationship("AuditLog", back_populates="transaction")
    erp_postings = relationship("ERPPosting", back_populates="transaction")

    def __repr__(self):
        return f"<Transaction #{self.id}: {self.description[:40]}>"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    predicted_gl_code = Column(String(10), nullable=False)
    predicted_gl_name = Column(String(200), nullable=True)
    confidence_score = Column(Float, nullable=False)
    status = Column(
        String(30), nullable=False, default="pending",
        # Values: auto_posted | pending_review | manual_required | approved | rejected
    )
    routed_action = Column(String(30), nullable=True)
    top_candidates = Column(Text, nullable=True)  # JSON string of top-K candidates
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="predictions")
    corrections = relationship("Correction", back_populates="prediction")

    def __repr__(self):
        return f"<Prediction TXN#{self.transaction_id} → {self.predicted_gl_code} ({self.confidence_score}%)>"


class Correction(Base):
    __tablename__ = "corrections"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    original_gl_code = Column(String(10), nullable=False)
    corrected_gl_code = Column(String(10), nullable=False)
    corrected_by = Column(String(100), nullable=True, default="analyst")
    reason = Column(Text, nullable=True)
    used_for_retrain = Column(Integer, default=0)  # 0 = not yet, 1 = used
    created_at = Column(DateTime, default=datetime.utcnow)

    prediction = relationship("Prediction", back_populates="corrections")

    def __repr__(self):
        return f"<Correction {self.original_gl_code} → {self.corrected_gl_code}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    action = Column(String(50), nullable=False)
    # Actions: uploaded | predicted | auto_posted | sent_for_review |
    #          approved | rejected | corrected | retrained
    actor = Column(String(100), nullable=False, default="system")
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog [{self.action}] by {self.actor}>"


class ERPPosting(Base):
    __tablename__ = "erp_postings"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    gl_code = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    erp_response_code = Column(String(10), nullable=True)
    erp_response_message = Column(Text, nullable=True)
    posted_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="erp_postings")

    def __repr__(self):
        return f"<ERPPosting TXN#{self.transaction_id} → {self.gl_code}>"
