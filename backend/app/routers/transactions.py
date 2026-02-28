"""Transaction upload and listing endpoints."""

import csv
import io
import uuid
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction, ChartOfAccounts
from app.schemas import TransactionRead, TransactionUploadResponse, COARead, TransactionCreate
from app.utils.audit_logger import log_audit

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post("/upload", response_model=TransactionUploadResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel file of transactions."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(400, "Only CSV and Excel files are supported")

    contents = await file.read()
    batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"

    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    # Validate required columns
    required_cols = {"description", "amount"}
    if not required_cols.issubset(set(df.columns.str.lower())):
        raise HTTPException(400, f"File must contain columns: {required_cols}")

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    transactions_created = 0
    for _, row in df.iterrows():
        txn_date = row.get("transaction_date")
        if pd.isna(txn_date):
            txn_date = datetime.utcnow()
        elif isinstance(txn_date, str):
            try:
                txn_date = datetime.strptime(txn_date, "%Y-%m-%d")
            except ValueError:
                txn_date = datetime.utcnow()

        txn = Transaction(
            batch_id=batch_id,
            transaction_date=txn_date,
            description=str(row.get("description", "")),
            amount=float(row.get("amount", 0)),
            vendor=str(row.get("vendor", "")) if pd.notna(row.get("vendor")) else None,
            department=str(row.get("department", "")) if pd.notna(row.get("department")) else None,
            source_file=file.filename,
            created_at=datetime.utcnow(),
        )
        db.add(txn)
        transactions_created += 1

    db.commit()

    # Audit log
    log_audit(
        db, action="uploaded", actor="user",
        details=f"Uploaded {transactions_created} transactions from '{file.filename}' (batch: {batch_id})"
    )

    return TransactionUploadResponse(
        batch_id=batch_id,
        total_transactions=transactions_created,
        message=f"Successfully uploaded {transactions_created} transactions.",
    )


@router.post("", response_model=TransactionRead)
def create_transaction(
    txn_in: TransactionCreate,
    db: Session = Depends(get_db),
):
    """Manually create a single transaction."""
    txn = Transaction(
        transaction_date=txn_in.transaction_date or datetime.utcnow(),
        description=txn_in.description,
        amount=txn_in.amount,
        vendor=txn_in.vendor,
        department=txn_in.department,
        source_file="Manual Entry",
        created_at=datetime.utcnow(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    log_audit(
        db, action="uploaded", actor="user",
        details=f"Manually entered transaction ID {txn.id}"
    )

    return txn


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    skip: int = 0,
    limit: int = 50,
    batch_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List transactions with optional batch filter and pagination."""
    query = db.query(Transaction)
    if batch_id:
        query = query.filter(Transaction.batch_id == batch_id)
    return query.order_by(Transaction.id.desc()).offset(skip).limit(limit).all()


@router.get("/coa", response_model=list[COARead])
def list_chart_of_accounts(db: Session = Depends(get_db)):
    """List the full Chart of Accounts."""
    return db.query(ChartOfAccounts).order_by(ChartOfAccounts.gl_code).all()
