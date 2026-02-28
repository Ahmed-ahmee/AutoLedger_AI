"""
AutoLedger AI – FastAPI Application Entry Point.

Intelligent GL Classification & ERP Posting System.
"""

import csv
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import DATA_DIR
from app.database import init_db, SessionLocal
from app.models import ChartOfAccounts
from app.ml.pipeline import initialize_index_from_coa


def seed_chart_of_accounts():
    """Load Chart of Accounts from CSV into the database if empty."""
    db = SessionLocal()
    try:
        if db.query(ChartOfAccounts).count() > 0:
            return

        coa_file = DATA_DIR / "chart_of_accounts.csv"
        if not coa_file.exists():
            print("⚠ chart_of_accounts.csv not found – skipping COA seeding")
            return

        with open(coa_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = ChartOfAccounts(
                    gl_code=row["gl_code"],
                    gl_name=row["gl_name"],
                    category=row["category"],
                    sub_category=row.get("sub_category", ""),
                )
                db.add(entry)
        db.commit()
        print(f"✓ Chart of Accounts seeded ({db.query(ChartOfAccounts).count()} entries)")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print("🚀 Starting AutoLedger AI...")
    init_db()
    seed_chart_of_accounts()
    initialize_index_from_coa()
    print("✓ Application ready!")
    yield
    # Shutdown
    print("🛑 Shutting down AutoLedger AI...")


# ── FastAPI App ────────────────────────────────────────────────────────
app = FastAPI(
    title="AutoLedger AI",
    description="Intelligent GL Classification & ERP Posting System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──────────────────────────────────────────────────
from app.routers import transactions, predictions, reviews, audit, erp  # noqa: E402

app.include_router(transactions.router)
app.include_router(predictions.router)
app.include_router(reviews.router)
app.include_router(audit.router)
app.include_router(erp.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "AutoLedger AI",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Intelligent GL Classification & ERP Posting System",
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "healthy"}

# ── Serve Frontend ───────────────────────────────────────────────────
# Mount static files (JS, CSS, images)
# Note: In production/Docker, the path will be /app/frontend
import os
from fastapi.responses import FileResponse

frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))

app.mount("/static", StaticFiles(directory=frontend_path), name="static")
# We also need to serve the frontend root for common assets if they aren't in /static
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
