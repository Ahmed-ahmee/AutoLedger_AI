"""Confidence scoring logic for GL code predictions."""


def compute_confidence(
    distances: list[float],
    gl_codes: list[str],
    k: int = 5,
) -> tuple[float, str]:
    """
    Compute a confidence score from FAISS search results.

    The score combines:
      - Distance-based similarity (60% weight): How close are the nearest vectors?
      - Frequency weighting (40% weight): Does the top GL code dominate the neighbors?

    Args:
        distances: L2 distances from FAISS (lower = more similar)
        gl_codes: GL codes of the K nearest neighbors
        k: Number of neighbors considered

    Returns:
        (confidence_percentage, top_gl_code)
    """
    if not distances or not gl_codes:
        return 0.0, "0000"

    # 1. Distance → similarity (0–1), using inverse transform
    similarities = [1.0 / (1.0 + d) for d in distances]

    # 2. Frequency: how often does the top code appear among neighbors?
    top_code = max(set(gl_codes), key=gl_codes.count)
    frequency_ratio = gl_codes.count(top_code) / max(len(gl_codes), 1)

    # 3. Weighted average → confidence percentage
    avg_similarity = sum(similarities) / len(similarities)
    confidence = 0.6 * avg_similarity + 0.4 * frequency_ratio

    return round(confidence * 100, 2), top_code
