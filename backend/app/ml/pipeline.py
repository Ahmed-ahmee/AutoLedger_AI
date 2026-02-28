"""End-to-end ML pipeline: text → embedding → FAISS search → prediction."""

import csv
from pathlib import Path

import numpy as np

from app.config import DATA_DIR, FAISS_TOP_K
from app.ml.embeddings import encode_text, encode_texts, build_transaction_text
from app.ml.vector_store import (
    add_vectors, search, save_index, get_total_vectors, get_index
)
from app.services.confidence import compute_confidence


def initialize_index_from_coa():
    """
    Seed the FAISS index using the Chart of Accounts.
    Each GL code gets an embedding from its name + category.
    """
    coa_file = DATA_DIR / "chart_of_accounts.csv"
    if not coa_file.exists():
        print(f"⚠ COA file not found: {coa_file}")
        return

    texts = []
    labels = []

    with open(coa_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = f"{row['gl_name']} {row['category']} {row['sub_category']}"
            texts.append(text)
            labels.append({
                "gl_code": row["gl_code"],
                "gl_name": row["gl_name"],
                "text": text,
            })

    if not texts:
        print("⚠ No COA entries found")
        return

    embeddings = encode_texts(texts)
    add_vectors(embeddings, labels)

    # Also add enriched variations for better matching
    _add_enriched_coa_vectors()

    # Seed with real transaction data if available
    _add_kaggle_transactions()

    save_index()
    print(f"✓ FAISS index initialized with {get_total_vectors()} vectors from COA")

def _add_kaggle_transactions():
    """Seed the FAISS index using unique descriptions from kaggle_transactions.csv."""
    import pandas as pd
    kaggle_file = DATA_DIR / "kaggle_transactions.csv"
    if not kaggle_file.exists():
        return
        
    try:
        df = pd.read_csv(kaggle_file)
        # We only really need unique descriptions for the index
        unique_txns = df.drop_duplicates(subset=["description"]).dropna(subset=["description", "true_gl_code"])
        
        # Load COA for gl_name lookup
        coa_lookup = {}
        coa_file = DATA_DIR / "chart_of_accounts.csv"
        with open(coa_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                coa_lookup[row["gl_code"]] = row["gl_name"]
                
        all_texts = []
        all_labels = []
        
        for _, row in unique_txns.iterrows():
            gl_code = str(row["true_gl_code"])
            desc = str(row["description"])
            gl_name = coa_lookup.get(gl_code, "Unknown")
            
            all_texts.append(desc)
            all_labels.append({
                "gl_code": gl_code,
                "gl_name": gl_name,
                "text": desc,
            })
            
        if all_texts:
            embeddings = encode_texts(all_texts)
            add_vectors(embeddings, all_labels)
            print(f"✓ Added {len(all_texts)} unique Kaggle transactions to index")
    except Exception as e:
        print(f"⚠ Failed to load Kaggle data: {e}")


def _add_enriched_coa_vectors():
    """Add additional description-style vectors for each GL code to improve matching."""
    enrichment_map = {
        "1100": [
            "bank transfer deposit wire ACH",
            "cash withdrawal petty cash bank interest",
        ],
        "1200": [
            "accounts receivable customer invoice payment due",
            "client billing outstanding balance trade receivable",
        ],
        "1300": [
            "inventory purchase raw materials stock warehouse",
            "procurement supply chain goods merchandise",
        ],
        "2100": [
            "accounts payable vendor invoice supplier bill",
            "trade payable procurement outstanding balance",
        ],
        "2200": [
            "accrued expenses wages interest tax bonus",
            "accrued liability provision charges",
        ],
        "3100": [
            "retained earnings dividend net income equity",
        ],
        "4100": [
            "product sales revenue wholesale retail order",
            "merchandise sold point of sale licensing",
        ],
        "4200": [
            "service revenue consulting advisory retainer",
            "professional services implementation contract",
        ],
        "5100": [
            "office supplies stationery printer paper toner",
            "desk accessories breakroom supplies pens",
        ],
        "5200": [
            "travel expense flight hotel car rental",
            "business trip accommodation per diem uber",
        ],
        "5300": [
            "utility expense electricity water gas internet",
            "telephone VoIP service charges",
        ],
        "5400": [
            "software subscription SaaS license cloud hosting",
            "annual renewal platform developer tools",
        ],
        "5500": [
            "professional fees legal accounting audit consulting",
            "tax preparation HR external advisory",
        ],
        "5600": [
            "commission sales referral bonus agent payout",
            "channel partner performance incentive",
        ],
        "5700": [
            "rent expense office lease warehouse co-working space",
            "parking facility storage property rent",
        ],
        "5800": [
            "marketing expense advertising campaign social media",
            "trade show content email influencer promotion",
        ],
        "5900": [
            "salary expense payroll wages compensation",
            "bi-weekly pay overtime contractor payment",
        ],
        "6100": [
            "insurance premium general liability workers compensation",
            "property insurance D&O cyber policy",
        ],
        "6200": [
            "depreciation expense equipment computer furniture",
            "vehicle fleet amortization leasehold",
        ],
    }

    # Load COA for gl_name lookup
    coa_lookup = {}
    coa_file = DATA_DIR / "chart_of_accounts.csv"
    with open(coa_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            coa_lookup[row["gl_code"]] = row["gl_name"]

    all_texts = []
    all_labels = []

    for gl_code, descriptions in enrichment_map.items():
        gl_name = coa_lookup.get(gl_code, "")
        for desc in descriptions:
            all_texts.append(desc)
            all_labels.append({
                "gl_code": gl_code,
                "gl_name": gl_name,
                "text": desc,
            })

    if all_texts:
        embeddings = encode_texts(all_texts)
        add_vectors(embeddings, all_labels)


def classify_transaction(
    description: str,
    vendor: str = "",
    department: str = "",
    k: int = FAISS_TOP_K,
) -> dict:
    """
    Classify a single transaction.

    Returns:
        {
            predicted_gl_code: str,
            predicted_gl_name: str,
            confidence_score: float,
            top_candidates: [{gl_code, gl_name, score}, ...]
        }
    """
    text = build_transaction_text(description, vendor, department)
    query_vector = encode_text(text)

    distances, results = search(query_vector, k=k)

    if not results:
        return {
            "predicted_gl_code": "0000",
            "predicted_gl_name": "Unclassified",
            "confidence_score": 0.0,
            "top_candidates": [],
        }

    gl_codes = [r["gl_code"] for r in results]
    gl_names = {r["gl_code"]: r["gl_name"] for r in results}

    confidence, top_code = compute_confidence(distances, gl_codes, k=len(results))

    # Build top candidates with individual scores
    seen = set()
    top_candidates = []
    for dist, res in zip(distances, results):
        code = res["gl_code"]
        if code not in seen:
            seen.add(code)
            score = round(100 / (1 + dist), 2)
            top_candidates.append({
                "gl_code": code,
                "gl_name": res["gl_name"],
                "score": score,
            })

    # Sort by score descending
    top_candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "predicted_gl_code": top_code,
        "predicted_gl_name": gl_names.get(top_code, ""),
        "confidence_score": confidence,
        "top_candidates": top_candidates[:3],
    }
