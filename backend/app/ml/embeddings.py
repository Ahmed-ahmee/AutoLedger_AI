"""Sentence-Transformer embedding wrapper."""

from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION

# Global model instance (loaded once)
_model = None


def get_model() -> SentenceTransformer:
    """Lazy-load and return the sentence-transformer model."""
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("✓ Model loaded successfully.")
    return _model


def encode_text(text: str) -> np.ndarray:
    """Encode a single text string into a dense vector."""
    model = get_model()
    embedding = model.encode([text], normalize_embeddings=True)
    return embedding[0].astype(np.float32)


def encode_texts(texts: list[str]) -> np.ndarray:
    """Encode a batch of text strings into dense vectors."""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.astype(np.float32)


def build_transaction_text(description: str, vendor: str = "", department: str = "") -> str:
    """Combine transaction fields into a single text for embedding."""
    parts = [description]
    if vendor:
        parts.append(f"vendor: {vendor}")
    if department:
        parts.append(f"department: {department}")
    return " | ".join(parts)
