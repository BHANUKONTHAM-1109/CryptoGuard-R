"""Tests for AI phishing detection."""

import pytest
from pathlib import Path

# Ensure backend is on path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_phishing_score_spam():
    """Spam-like text should have high phishing score."""
    from app.ai.phishing_model import get_model, get_phishing_score
    model = get_model()
    if model is None:
        pytest.skip("Model not trained")
    score = get_phishing_score(model, "Free prize! Click here to win! Urgent!")
    assert score >= 0.7


def test_phishing_score_legit():
    """Legitimate text should have low phishing score."""
    from app.ai.phishing_model import get_model, get_phishing_score
    model = get_model()
    if model is None:
        pytest.skip("Model not trained")
    score = get_phishing_score(model, "Meeting at 3pm tomorrow in the office.")
    assert score <= 0.5


def test_load_dataset():
    """Dataset should load with text and label columns."""
    from app.ai.phishing_model import load_dataset, _find_dataset
    path = _find_dataset()
    if path is None:
        pytest.skip("No dataset found")
    df = load_dataset(path)
    assert "text" in df.columns
    assert "label" in df.columns
    assert len(df) > 0
