# AutoLedger AI

> **Intelligent GL Classification & ERP Posting System**
> 
> AI-powered financial transaction classification using embedding-based ML, with confidence-gated routing and human-in-the-loop learning.

---

## 🎯 Overview

AutoLedger AI automates General Ledger (GL) code assignment for financial transactions. It uses **sentence-transformer embeddings** + **FAISS vector search** to predict GL codes, applies confidence-based routing (auto-post / human review / manual), and continuously learns from corrections.

### Key Features

- **CSV/Excel Upload** – Drag-and-drop transaction ingestion
- **ML Classification** – Embedding-based similarity search (all-MiniLM-L6-v2 + FAISS)
- **Confidence Scoring** – Distance + frequency weighted scoring
- **Smart Routing** – Auto-post (>80%), human review (50–80%), manual (<50%)
- **Mock ERP Posting** – Simulated ERP API with journal entries
- **Human-in-the-Loop** – Review queue with approve/reject & correction
- **Retraining Loop** – Incremental FAISS updates from corrections
- **Full Audit Trail** – Every action logged with timestamp and actor
- **Real-time Dashboard** – KPIs, classification breakdown, ML status

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Presentation Layer                       │
│           Tailwind CSS Dashboard (SPA)                  │
├─────────────────────────────────────────────────────────┤
│                    API Layer                             │
│           FastAPI REST Endpoints                        │
├─────────────────────────────────────────────────────────┤
│                  Service Layer                           │
│   Classifier │ Confidence │ Router │ Retrainer │ ERP    │
├─────────────────────────────────────────────────────────┤
│                    ML Layer                              │
│      Sentence-Transformers  │  FAISS Vector Index       │
├─────────────────────────────────────────────────────────┤
│                   Data Layer                             │
│          SQLite (SQLAlchemy ORM) │ File Storage          │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/AutoLedger_AI.git
cd AutoLedger_AI

# Install dependencies (assuming you are in a virtual environment)
pip install -r backend/requirements.txt

# Generate synthetic dataset (1,000 transactions)
cd backend
python scripts/generate_dataset.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: Open `frontend/index.html` in your browser

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python) |
| ML Model | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Search | FAISS (Facebook AI Similarity Search) |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | Tailwind CSS + Vanilla JS |
| Data Processing | Pandas, NumPy |

---

## 📁 Project Structure

```
AutoLedger_AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings & thresholds
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # ORM models (6 tables)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   ├── ml/                  # Embeddings + FAISS
│   │   └── utils/               # Audit logger
│   ├── data/                    # CSVs + FAISS index + DB
│   ├── scripts/                 # Dataset generator
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Dashboard (SPA)
│   ├── app.js                   # Frontend logic
│   └── styles.css               # Custom styles
└── README.md
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/transactions/upload` | Upload CSV/Excel transactions |
| `GET` | `/api/transactions` | List transactions |
| `GET` | `/api/transactions/coa` | Chart of Accounts |
| `POST` | `/api/predictions/classify` | Classify & route transactions |
| `GET` | `/api/predictions` | List predictions (filterable) |
| `GET` | `/api/reviews/queue` | Pending review items |
| `POST` | `/api/reviews/{id}/approve` | Approve prediction |
| `POST` | `/api/reviews/{id}/reject` | Reject & correct |
| `GET` | `/api/audit/logs` | Audit trail |
| `POST` | `/api/ml/retrain` | Trigger retraining |
| `GET` | `/api/dashboard/stats` | Dashboard KPIs |

---

## 🧠 ML Pipeline

1. **Seed** – Chart of Accounts → embeddings → FAISS index
2. **Enrich** – Keyword-augmented vectors for each GL code
3. **Embed** – New transaction `description + vendor + dept` → 384-dim vector
4. **Search** – FAISS top-K (K=5) nearest neighbors
5. **Score** – `0.6 × avg_similarity + 0.4 × frequency_ratio`
6. **Route** – Confidence thresholds: >80% auto | 50–80% review | <50% manual

---

## 🔄 Human-in-the-Loop Workflow

```
Transaction → ML Prediction → Confidence Check
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
               Auto-Post    Review Queue    Manual Entry
               (>80%)       (50–80%)        (<50%)
                    │             │             │
                    ▼             ▼             ▼
               ERP Post    Approve/Reject   Correction
                    │             │             │
                    └─────────────┴─────────────┘
                                  │
                            Audit Trail
                                  │
                          Retrain on Corrections
```

---

## 🗄️ Database Schema

| Table | Description |
|---|---|
| `chart_of_accounts` | GL codes with categories |
| `transactions` | Uploaded financial transactions |
| `predictions` | ML predictions with confidence scores |
| `corrections` | Human corrections (feedback loop) |
| `audit_logs` | Complete system activity trail |
| `erp_postings` | Mock ERP posting records |

---

## 🗺️ Future Roadmap

| Phase | Enhancement |
|---|---|
| v1.1 | Multi-model ensemble (XGBoost + embeddings) |
| v1.2 | Real ERP integration (SAP, Oracle, NetSuite) |
| v1.3 | Role-based access control (JWT auth) |
| v1.4 | Multi-currency & multi-entity support |
| v2.0 | LLM-powered natural language querying |
| v2.1 | Anomaly detection for unusual transactions |
| v2.2 | Batch scheduling & automated ingestion |
| v2.3 | Docker + Kubernetes deployment |

---

## 📄 License

MIT License
