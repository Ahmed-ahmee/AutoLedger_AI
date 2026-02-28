"""FAISS vector index management for GL code similarity search."""

import json
import os

import faiss
import numpy as np

from app.config import EMBEDDING_DIMENSION, FAISS_INDEX_DIR, FAISS_TOP_K

# Global state
_index: faiss.IndexFlatL2 | None = None
_labels: list[dict] = []  # [{gl_code, gl_name, text}, ...]
_LABELS_FILE = os.path.join(str(FAISS_INDEX_DIR), "labels.json")
_INDEX_FILE = os.path.join(str(FAISS_INDEX_DIR), "index.faiss")


def get_index() -> faiss.IndexFlatL2:
    """Return the FAISS index, creating one if needed."""
    global _index
    if _index is None:
        if os.path.exists(_INDEX_FILE):
            _index = faiss.read_index(_INDEX_FILE)
            _load_labels()
            print(f"✓ FAISS index loaded from disk ({_index.ntotal} vectors)")
        else:
            _index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            print("✓ New FAISS index created")
    return _index


def _load_labels():
    """Load label metadata from disk."""
    global _labels
    if os.path.exists(_LABELS_FILE):
        with open(_LABELS_FILE, "r", encoding="utf-8") as f:
            _labels = json.load(f)


def _save_labels():
    """Persist label metadata to disk."""
    with open(_LABELS_FILE, "w", encoding="utf-8") as f:
        json.dump(_labels, f, indent=2, ensure_ascii=False)


def save_index():
    """Persist FAISS index to disk."""
    index = get_index()
    faiss.write_index(index, _INDEX_FILE)
    _save_labels()
    print(f"✓ FAISS index saved ({index.ntotal} vectors)")


def add_vectors(embeddings: np.ndarray, labels: list[dict]):
    """
    Add vectors to the FAISS index.

    Args:
        embeddings: (N, dim) float32 array
        labels: list of dicts with at least {gl_code, gl_name}
    """
    global _labels
    index = get_index()
    index.add(embeddings)
    _labels.extend(labels)


def search(query_vector: np.ndarray, k: int = FAISS_TOP_K) -> tuple[list[float], list[dict]]:
    """
    Search for the K nearest neighbors.

    Returns:
        distances: list of L2 distances
        results: list of label dicts for each neighbor
    """
    index = get_index()
    if index.ntotal == 0:
        return [], []

    # Ensure proper shape
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)

    actual_k = min(k, index.ntotal)
    distances, indices = index.search(query_vector, actual_k)

    result_distances = distances[0].tolist()
    result_labels = [_labels[i] for i in indices[0] if i < len(_labels)]

    return result_distances, result_labels


def get_total_vectors() -> int:
    """Return the total number of vectors in the index."""
    return get_index().ntotal


def reset_index():
    """Reset the FAISS index (for testing)."""
    global _index, _labels
    _index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    _labels = []
