import pytest
import numpy as np

from app.database import init_db
from app.ml.vector_store import get_total_vectors, reset_index
from app.ml.pipeline import initialize_index_from_coa, classify_transaction

def test_ml_pipeline():
    # Reset state
    reset_index()

    # 1. Seed index
    initialize_index_from_coa()
    total = get_total_vectors()
    assert total > 0, "Index should be seeded from COA and enrichments"

    # 2. Test explicit matching (e.g., flight should go to travel expense 5200)
    res = classify_transaction(
        description="Flight booking to New York",
        vendor="Delta Airlines",
        department="Sales"
    )

    assert res["predicted_gl_code"] == "5200"
    assert res["confidence_score"] > 0
    assert len(res["top_candidates"]) > 0
    assert res["top_candidates"][0]["gl_code"] == "5200"

    # 3. Test explicit matching (AWS should go to software 5400)
    res2 = classify_transaction(
        description="Monthly Cloud hosting charges",
        vendor="AWS",
        department="Engineering"
    )

    assert res2["predicted_gl_code"] == "5400"
