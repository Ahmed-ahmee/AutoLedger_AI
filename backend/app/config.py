"""Application configuration and settings."""

import os
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"
UPLOAD_DIR = DATA_DIR / "uploads"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Database ───────────────────────────────────────────────────────────
DATABASE_URL = f"sqlite:///{DATA_DIR / 'autoledger.db'}"

# ── ML Settings ────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
FAISS_TOP_K = 5

# ── Confidence Thresholds ─────────────────────────────────────────────
CONFIDENCE_AUTO_POST = 80.0     # > 80% → auto-post to ERP
CONFIDENCE_REVIEW = 50.0        # 50–80% → human review
# < 50% → manual classification

# ── Retraining ─────────────────────────────────────────────────────────
RETRAIN_CORRECTION_THRESHOLD = 10  # retrain after N new corrections

# ── Mock ERP ───────────────────────────────────────────────────────────
ERP_SUCCESS_RATE = 0.95  # 95% mock success rate
