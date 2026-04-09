"""
CryptoGuard-R - NLP Preprocessing
Tokenization, cleaning, and feature extraction for phishing detection.
"""

import re
import string
from typing import List

# NLTK imports - download required data on first use
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer

    def _ensure_nltk_data() -> None:
        try:
            stopwords.words("english")
        except LookupError:
            nltk.download("stopwords", quiet=True)
        try:
            word_tokenize("test")
        except LookupError:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
        try:
            WordNetLemmatizer().lemmatize("test")
        except LookupError:
            nltk.download("wordnet", quiet=True)
            nltk.download("averaged_perceptron_tagger", quiet=True)

    _ensure_nltk_data()
    _STOP = set(stopwords.words("english"))
    _LEMMATIZER = WordNetLemmatizer()
except ImportError:
    _STOP = set()
    _LEMMATIZER = None


def clean_text(text: str) -> str:
    """
    Normalize and clean input text.
    - Lowercase, strip whitespace
    - Remove URLs, emails (common phishing indicators)
    - Remove excessive punctuation
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # Remove email-like patterns
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    # Remove digits (optional - can keep for "100% free" etc.)
    # text = re.sub(r'\d+', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """Tokenize into words, remove stopwords, lemmatize."""
    text = clean_text(text)
    if not text:
        return []
    try:
        tokens = word_tokenize(text)
    except Exception:
        tokens = text.split()
    tokens = [t for t in tokens if t not in string.punctuation and len(t) > 1]
    tokens = [t for t in tokens if t.lower() not in _STOP]
    if _LEMMATIZER:
        tokens = [_LEMMATIZER.lemmatize(t) for t in tokens]
    return tokens


def tokens_to_string(tokens: List[str]) -> str:
    """Join tokens for TF-IDF input (sklearn expects strings)."""
    return " ".join(tokens)


def preprocess_for_model(text: str) -> str:
    """
    Full pipeline: clean + tokenize + rejoin.
    Use this before feeding to TF-IDF vectorizer.
    """
    tokens = tokenize(text)
    return tokens_to_string(tokens)
