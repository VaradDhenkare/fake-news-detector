"""
model_training.py  —  TruthLens ML Service
===========================================
Trains a high-accuracy Fake News Detection model with MLOps artifact tracking.

Pipeline:
  1. Load dataset (data/news.csv or WELFake_Dataset.csv -> 'text' + 'label' columns)
  2. Preprocess text (lowercase, regex URL strip, punctuation removal, stopword filtering)
  3. Dual TF-IDF vectorization:
       - Word n-grams (1, 2)
       - Character n-grams (3, 5)
       - Combined via scipy.sparse.hstack
  4. Train calibrated LinearSVC / Logistic Regression ensemble for probability output
  5. Evaluate accuracy, precision, recall, and F1-score
  6. Persist production artifacts:
       - artifacts/fake_news_model.pkl
       - artifacts/tfidf_vectorizer.pkl
       - artifacts/metrics.json (read by FastAPI /metrics endpoint)
       - artifacts/model.joblib & vectorizer.joblib (for backward compatibility)

Run:
    python model_training.py
"""

import os
import re
import json
import string
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

import joblib
import numpy as np
import pandas as pd
import scipy.sparse
import nltk

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# ---------------------------------------------------------------------------
# NLTK Stopwords
# ---------------------------------------------------------------------------
nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))

# ---------------------------------------------------------------------------
# Artifact & Data Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
DATASET_PATH = os.path.join(DATA_DIR, "news.csv")
WELFAKE_PATH = os.path.join(DATA_DIR, "WELFake_Dataset.csv")

MODEL_PKL_PATH = os.path.join(ARTIFACTS_DIR, "fake_news_model.pkl")
VECTORIZER_PKL_PATH = os.path.join(ARTIFACTS_DIR, "tfidf_vectorizer.pkl")
METRICS_JSON_PATH = os.path.join(ARTIFACTS_DIR, "metrics.json")

# Legacy compatibility paths
MODEL_JOBLIB_PATH = os.path.join(ARTIFACTS_DIR, "model.joblib")
VECTORIZER_JOBLIB_PATH = os.path.join(ARTIFACTS_DIR, "vectorizer.joblib")


# ---------------------------------------------------------------------------
# Text Preprocessing
# ---------------------------------------------------------------------------
def preprocess_text(text: str) -> str:
    """Cleans text: lowercase, removes URLs, removes punctuation/digits, filters stopwords."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation + string.digits))
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in STOP_WORDS and len(t) > 2]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Dataset Loader
# ---------------------------------------------------------------------------
def load_dataset(path: str = DATASET_PATH) -> pd.DataFrame:
    """Loads and standardizes dataset into columns ['text', 'label']."""
    target_path = path
    if not os.path.exists(target_path) and os.path.exists(WELFAKE_PATH):
        target_path = WELFAKE_PATH

    print(f"[INFO] Loading dataset from: {target_path}")
    df = pd.read_csv(target_path, on_bad_lines="skip")
    df.columns = [c.strip().lower() for c in df.columns]

    # Handle WELFake format (title, text, label where 0=real, 1=fake or vice-versa)
    if "label" in df.columns and pd.api.types.is_numeric_dtype(df["label"]):
        # In WELFake: 1 = fake, 0 = real
        df["label"] = df["label"].map({1: "FAKE", 0: "REAL"})

    if "title" in df.columns and "text" in df.columns:
        df["text"] = df["title"].fillna("") + " " + df["text"].fillna("")
    elif "text" not in df.columns:
        raise ValueError("Dataset must contain a 'text' column.")

    if "label" not in df.columns:
        raise ValueError("Dataset must contain a 'label' column.")

    df["label"] = df["label"].astype(str).str.strip().str.upper()
    df = df[df["label"].isin(["FAKE", "REAL"])].copy()
    df.dropna(subset=["text", "label"], inplace=True)
    df = df[df["text"].str.len() > 20]

    print(f"[INFO] Dataset loaded: {len(df):,} samples")
    print(f"[INFO] Label distribution:\n{df['label'].value_counts()}\n")
    return df


# ---------------------------------------------------------------------------
# Feature Extraction (Dual TF-IDF: Word + Character)
# ---------------------------------------------------------------------------
def build_features(
    X_train: np.ndarray, X_test: np.ndarray
) -> Tuple[scipy.sparse.csr_matrix, scipy.sparse.csr_matrix, TfidfVectorizer, TfidfVectorizer]:
    """
    Builds word-level (1, 2 n-grams) and char-level (3, 5 n-grams) TF-IDF features.
    Combined via sparse hstack for robust signal extraction.
    """
    print("[INFO] Fitting word-level TF-IDF (1, 2-grams)...")
    word_vec = TfidfVectorizer(
        max_features=60_000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
        analyzer="word",
        strip_accents="unicode",
    )
    Xw_train = word_vec.fit_transform(X_train)
    Xw_test = word_vec.transform(X_test)

    print("[INFO] Fitting char-level TF-IDF (3, 5-grams)...")
    char_vec = TfidfVectorizer(
        max_features=25_000,
        ngram_range=(3, 5),
        sublinear_tf=True,
        min_df=2,
        analyzer="char_wb",
        strip_accents="unicode",
    )
    Xc_train = char_vec.fit_transform(X_train)
    Xc_test = char_vec.transform(X_test)

    X_train_feat = scipy.sparse.hstack([Xw_train, Xc_train], format="csr")
    X_test_feat = scipy.sparse.hstack([Xw_test, Xc_test], format="csr")

    print(f"[INFO] Feature matrix shape: train={X_train_feat.shape} test={X_test_feat.shape}")
    return X_train_feat, X_test_feat, word_vec, char_vec


# ---------------------------------------------------------------------------
# Classifier Builder
# ---------------------------------------------------------------------------
def build_classifier() -> CalibratedClassifierCV:
    """Wraps LinearSVC with CalibratedClassifierCV for probabilistic calibration."""
    base = LinearSVC(
        C=1.0,
        max_iter=5000,
        class_weight="balanced",
        random_state=42,
    )
    return CalibratedClassifierCV(base, cv=3)


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------
def train(dataset_path: str = DATASET_PATH) -> Dict[str, Any]:
    """Executes full training pipeline, evaluates metrics, and persists artifacts."""
    df = load_dataset(dataset_path)

    print("[INFO] Preprocessing text...")
    df["clean_text"] = df["text"].apply(preprocess_text)

    X = df["clean_text"].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"[INFO] Train split: {len(X_train):,} | Test split: {len(X_test):,}")

    X_train_feat, X_test_feat, word_vec, char_vec = build_features(X_train, X_test)

    print("[INFO] Training calibrated LinearSVC classifier...")
    model = build_classifier()
    model.fit(X_train_feat, y_train)

    # Evaluation
    y_pred = model.predict(X_test_feat)
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    recall = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    print("\n" + "=" * 60)
    print("  PRODUCTION MODEL EVALUATION")
    print("=" * 60)
    print(f"  Accuracy  : {accuracy * 100:.2f}%")
    print(f"  Precision : {precision * 100:.2f}%")
    print(f"  Recall    : {recall * 100:.2f}%")
    print(f"  F1 Score  : {f1 * 100:.2f}%")
    print("=" * 60)
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=["FAKE", "REAL"]))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    # Persist artifacts
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    vectorizer_bundle = {"word": word_vec, "char": char_vec}

    # Save .pkl artifacts required by Task 1
    joblib.dump(model, MODEL_PKL_PATH)
    joblib.dump(vectorizer_bundle, VECTORIZER_PKL_PATH)

    # Save legacy .joblib artifacts for backward compatibility
    joblib.dump(model, MODEL_JOBLIB_PATH)
    joblib.dump(vectorizer_bundle, VECTORIZER_JOBLIB_PATH)

    model_version = os.environ.get("MODEL_VERSION", "1.0.0")
    training_date = datetime.now(timezone.utc).isoformat()

    metrics_payload = {
        "model_version": model_version,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "training_date": training_date,
        "last_trained_at": training_date,
        "dataset_size": len(df),
        "test_size": len(y_test),
        "algorithm": "Dual-TFIDF-CalibratedLinearSVC",
        "domain_ontology": "Bruviti-Service-Triage-v1",
        "class_metrics": {
            "fake": {
                "precision": round(float(precision_score(y_test, y_pred, pos_label="FAKE", zero_division=0)), 4),
                "recall": round(float(recall_score(y_test, y_pred, pos_label="FAKE", zero_division=0)), 4),
                "f1": round(float(f1_score(y_test, y_pred, pos_label="FAKE", zero_division=0)), 4),
            },
            "real": {
                "precision": round(float(precision_score(y_test, y_pred, pos_label="REAL", zero_division=0)), 4),
                "recall": round(float(recall_score(y_test, y_pred, pos_label="REAL", zero_division=0)), 4),
                "f1": round(float(f1_score(y_test, y_pred, pos_label="REAL", zero_division=0)), 4),
            },
        },
    }

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print(f"\n[INFO] Model saved      -> {MODEL_PKL_PATH}")
    print(f"[INFO] Vectorizer saved -> {VECTORIZER_PKL_PATH}")
    print(f"[INFO] Metrics saved    -> {METRICS_JSON_PATH}")
    print("\nTraining and artifact persistence complete.")
    return metrics_payload


if __name__ == "__main__":
    if not os.path.exists(DATASET_PATH) and not os.path.exists(WELFAKE_PATH):
        raise FileNotFoundError(f"Dataset missing in {DATA_DIR}. Run download_dataset.py first.")
    train()
