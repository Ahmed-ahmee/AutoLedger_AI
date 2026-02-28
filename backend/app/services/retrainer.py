"""
Retraining loop – gathers corrections, embeds, and adds to FAISS index.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Correction, Prediction, Transaction, AuditLog
from app.ml.embeddings import encode_texts, build_transaction_text
from app.ml.vector_store import add_vectors, save_index, get_total_vectors


def retrain_from_corrections(db: Session) -> dict:
    """
    Incremental retraining: take all unused corrections and add them
    to the FAISS index so future predictions benefit from human feedback.

    Returns:
        {corrections_used: int, new_vectors_added: int}
    """
    # Find corrections not yet used for retraining
    corrections = (
        db.query(Correction)
        .filter(Correction.used_for_retrain == 0)
        .all()
    )

    if not corrections:
        return {"corrections_used": 0, "new_vectors_added": 0, "message": "No new corrections to retrain on."}

    texts = []
    labels = []

    for correction in corrections:
        # Get the original transaction
        prediction = db.query(Prediction).get(correction.prediction_id)
        if not prediction:
            continue
        transaction = db.query(Transaction).get(prediction.transaction_id)
        if not transaction:
            continue

        text = build_transaction_text(
            transaction.description,
            transaction.vendor or "",
            transaction.department or "",
        )
        texts.append(text)
        labels.append({
            "gl_code": correction.corrected_gl_code,
            "gl_name": "",  # Will be filled by consumers
            "text": text,
            "source": "correction",
        })

    if texts:
        # Encode and add to FAISS
        embeddings = encode_texts(texts)
        add_vectors(embeddings, labels)
        save_index()

        # Mark corrections as used
        for correction in corrections:
            correction.used_for_retrain = 1
        db.commit()

    # Audit log
    audit = AuditLog(
        transaction_id=None,
        action="retrained",
        actor="system",
        details=f"Retrained with {len(texts)} corrections. Total vectors: {get_total_vectors()}",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()

    return {
        "corrections_used": len(corrections),
        "new_vectors_added": len(texts),
        "total_vectors": get_total_vectors(),
        "message": f"Successfully retrained with {len(texts)} corrections.",
    }
