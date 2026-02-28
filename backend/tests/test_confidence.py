import pytest
from app.services.confidence import compute_confidence

def test_compute_confidence():
    # 1. High confidence case: highly similar neighbors, all agree
    distances = [0.1, 0.15, 0.2]
    gl_codes = ["5100", "5100", "5100"]

    conf, top_code = compute_confidence(distances, gl_codes, k=3)
    assert top_code == "5100"
    assert conf > 80.0  # Should be easily above auto-post threshold

    # 2. Medium confidence case: mixed distances, slight disagreement
    distances = [0.4, 0.6, 0.8]
    gl_codes = ["5200", "5200", "5500"]

    conf, top_code = compute_confidence(distances, gl_codes, k=3)
    assert top_code == "5200"
    assert 50.0 < conf < 80.0  # Review queue material

    # 3. Low confidence case: far distances, complete disagreement
    distances = [1.5, 2.0, 2.5]
    gl_codes = ["5100", "5200", "5300"]

    conf, top_code = compute_confidence(distances, gl_codes, k=3)
    # frequency ratio is 1/3 (0.33)
    # similarity is low (~0.3)
    # Total should be around 31%
    assert conf < 50.0  # Manual required

    # 4. Edge case: Empty
    conf, top_code = compute_confidence([], [], k=3)
    assert conf == 0.0
    assert top_code == "0000"
