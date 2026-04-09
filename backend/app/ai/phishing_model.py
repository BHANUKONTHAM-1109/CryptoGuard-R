"""
CryptoGuard-R - AI Phishing Detection Model
Load dataset, NLP preprocessing, train ML model, save/load, inference.
"""

import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

from app.ai.nlp_utils import preprocess_for_model
from app.core.logging import get_logger

logger = get_logger("phishing_model")

# Label mapping: phishing/spam=1, legitimate/ham=0
PHISHING_LABEL = 1
LEGIT_LABEL = 0


def _find_dataset() -> Optional[Path]:
    """Locate dataset: phishing_emails.csv or spam.csv (SMS format)."""
    base = Path(__file__).resolve().parent.parent.parent.parent  # cryptoguard-r/
    candidates = [
        base / "datasets" / "phishing_emails.csv",
        base / "datasets" / "spam.csv",
        base / "spam.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_dataset(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load dataset. Supports:
    - phishing_emails.csv: columns 'text' (or email_text, message), 'label' (1/0)
    - spam.csv (UCI SMS): columns v1 (ham/spam), v2 (message)
    """
    p = path or _find_dataset()
    if not p or not p.exists():
        raise FileNotFoundError(
            f"No dataset found. Place phishing_emails.csv or spam.csv in datasets/"
        )
    df = pd.read_csv(p, encoding="utf-8", encoding_errors="ignore")
    # Normalize columns
    text_col = None
    label_col = None
    for c in df.columns:
        c_lower = str(c).lower()
        if c_lower in ("text", "email_text", "message", "v2", "content"):
            text_col = c
        if c_lower in ("label", "is_phishing", "v1", "target"):
            label_col = c
    if text_col is None or label_col is None:
        # Fallback: assume first col is label, second is text
        cols = list(df.columns)
        if len(cols) >= 2:
            label_col, text_col = cols[0], cols[1]
        else:
            raise ValueError(f"Dataset must have text and label columns. Got: {cols}")
    df = df[[text_col, label_col]].copy()
    df.columns = ["text", "label_raw"]
    df["text"] = df["text"].astype(str).fillna("")
    # Map labels to 0/1
    def to_binary(v):
        if isinstance(v, (int, float)):
            return PHISHING_LABEL if v == 1 or v == 1.0 else LEGIT_LABEL
        s = str(v).lower().strip()
        if s in ("spam", "phishing", "phish", "1", "yes", "true"):
            return PHISHING_LABEL
        return LEGIT_LABEL

    df["label"] = df["label_raw"].apply(to_binary)
    df = df[df["text"].str.len() > 0].dropna(subset=["label"])
    return df[["text", "label"]]


def build_pipeline() -> Pipeline:
    """
    TF-IDF + LogisticRegression pipeline.
    Feature selection: TF-IDF captures discriminative terms (urgent, free, click, etc.).
    LogisticRegression: interpretable, well-calibrated probabilities for thresholding.
    """
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),  # Unigrams and bigrams capture phrases
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        preprocessor=preprocess_for_model,
    )
    clf = LogisticRegression(
        max_iter=1000,
        C=1.0,
        random_state=42,
        class_weight="balanced",
    )
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def train(
    dataset_path: Optional[Path] = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[Pipeline, float]:
    """Train model and return (pipeline, accuracy)."""
    df = load_dataset(dataset_path)
    logger.info("Loaded %d samples", len(df))
    X = df["text"].tolist()
    y = df["label"].tolist()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info("Accuracy: %.4f", acc)
    logger.info("Report:\n%s", classification_report(y_test, y_pred, target_names=["legit", "phishing"]))
    return pipeline, acc


def save_model(pipeline: Pipeline, path: Path) -> None:
    """Persist pipeline (vectorizer + classifier) to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info("Saved model to %s", path)


def load_model(path: Path) -> Pipeline:
    """Load pipeline from disk."""
    with open(path, "rb") as f:
        pipeline = pickle.load(f)
    return pipeline


def predict(pipeline: Pipeline, text: str) -> Tuple[int, float]:
    """
    Predict phishing probability.
    Returns (label, probability_of_phishing).
    """
    proba = pipeline.predict_proba([text])[0]
    # Assume classes [0, 1] -> proba[1] is P(phishing)
    idx = list(pipeline.classes_).index(PHISHING_LABEL) if PHISHING_LABEL in pipeline.classes_ else 1
    p_phish = float(proba[idx])
    label = PHISHING_LABEL if p_phish >= 0.5 else LEGIT_LABEL
    return label, p_phish


def get_phishing_score(pipeline: Pipeline, text: str) -> float:
    """Return probability that the text is phishing (0.0 to 1.0)."""
    _, score = predict(pipeline, text)
    return score


# Singleton for API use - lazy load
_model: Optional[Pipeline] = None


def get_model(model_path: Optional[Path] = None) -> Optional[Pipeline]:
    """Load model from disk. Returns None if not found (train first)."""
    global _model
    if _model is not None:
        return _model
    from app.core.config import settings
    path = Path(settings.model_path)
    if not path.is_absolute():
        base = Path(__file__).resolve().parent.parent.parent  # backend/
        path = base / path
    if not path.exists():
        logger.warning("Model not found at %s; run train_and_save() first", path)
        return None
    _model = load_model(path)
    return _model


def train_and_save(model_path: Optional[Path] = None) -> Tuple[Pipeline, float]:
    """Train model and save to configured path. Returns (pipeline, accuracy)."""
    from app.core.config import settings
    path = Path(model_path or settings.model_path)
    if not path.is_absolute():
        base = Path(__file__).resolve().parent.parent.parent
        path = base / path
    pipeline, acc = train(dataset_path=_find_dataset())
    save_model(pipeline, path)
    return pipeline, acc
