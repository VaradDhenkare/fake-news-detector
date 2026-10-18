"""
predictor.py  —  TruthLens ML Service
======================================
Production Predictor singleton that loads calibrated model & vectorizer artifacts
and applies MLOps practices:
  - Artifact resolution (.pkl with fallback to .joblib)
  - Input validation (empty text rejection, max 10,000 chars, min 10 chars)
  - Confidence thresholding (< 0.65 -> UNCERTAIN)
  - Clean type-hinted interface
"""

import os
import re
import string
from typing import Dict, Any, Optional
import joblib
import numpy as np
import scipy.sparse
import nltk

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))

# ---------------------------------------------------------------------------
# Artifact Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

MODEL_PKL_PATH = os.path.join(ARTIFACTS_DIR, "fake_news_model.pkl")
VECTORIZER_PKL_PATH = os.path.join(ARTIFACTS_DIR, "tfidf_vectorizer.pkl")

# Fallback paths
MODEL_JOBLIB_PATH = os.path.join(ARTIFACTS_DIR, "model.joblib")
VECTORIZER_JOBLIB_PATH = os.path.join(ARTIFACTS_DIR, "vectorizer.joblib")

# Confidence threshold: predictions below this margin are flagged as UNCERTAIN
CONFIDENCE_THRESHOLD = 0.65
MAX_TEXT_LENGTH = 10000
MIN_TEXT_LENGTH = 10


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------
def preprocess_text(text: str) -> str:
    """Preprocess raw text to match model training pipeline."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation + string.digits))
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in STOP_WORDS and len(t) > 2]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Vectorization Helper
# ---------------------------------------------------------------------------
def vectorize_text(text: str, vec_bundle: Any) -> scipy.sparse.csr_matrix:
    """Transforms text using dual TF-IDF bundle (word + char) or single vectorizer."""
    if isinstance(vec_bundle, dict):
        word_feat = vec_bundle["word"].transform([text])
        char_feat = vec_bundle["char"].transform([text])
        return scipy.sparse.hstack([word_feat, char_feat], format="csr")
    return vec_bundle.transform([text])


# ---------------------------------------------------------------------------
# FakeNewsPredictor Singleton
# ---------------------------------------------------------------------------
class FakeNewsPredictor:
    """Singleton inference engine for TruthLens production service."""

    _instance: Optional["FakeNewsPredictor"] = None
    _model: Any = None
    _vec_bundle: Any = None
    _loaded: bool = False

    def __new__(cls) -> "FakeNewsPredictor":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> None:
        """Loads serialized model and vectorizer artifacts into memory."""
        if self._loaded:
            return

        # Resolve model path
        model_path = MODEL_PKL_PATH if os.path.exists(MODEL_PKL_PATH) else MODEL_JOBLIB_PATH
        vec_path = VECTORIZER_PKL_PATH if os.path.exists(VECTORIZER_PKL_PATH) else VECTORIZER_JOBLIB_PATH

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model artifact not found at {MODEL_PKL_PATH} or {MODEL_JOBLIB_PATH}. "
                "Run: python model_training.py"
            )
        if not os.path.exists(vec_path):
            raise FileNotFoundError(
                f"Vectorizer artifact not found at {VECTORIZER_PKL_PATH} or {VECTORIZER_JOBLIB_PATH}. "
                "Run: python model_training.py"
            )

        self._model = joblib.load(model_path)
        self._vec_bundle = joblib.load(vec_path)
        self._loaded = True

    def validate_input(self, text: str) -> str:
        """Validates incoming text according to production MLOps guidelines."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text cannot be empty.")
        stripped = text.strip()
        if len(stripped) > MAX_TEXT_LENGTH:
            raise ValueError(
                f"Input text exceeds maximum allowed limit of {MAX_TEXT_LENGTH} characters "
                f"(received {len(stripped)} chars)."
            )
        if len(stripped) < MIN_TEXT_LENGTH:
            raise ValueError(
                f"Input text too short for reliable classification "
                f"(minimum {MIN_TEXT_LENGTH} characters required)."
            )
        return stripped

    def predict(self, news_text: str) -> Dict[str, Any]:
        """
        Executes prediction with input validation, probability calibration,
        and confidence thresholding.

        Returns:
            {
                "label": "REAL" | "FAKE" | "UNCERTAIN",
                "prediction": "REAL" | "FAKE" | "UNCERTAIN",  # backward compatibility
                "raw_prediction": "REAL" | "FAKE",
                "confidence": float,
                "probabilities": {"FAKE": float, "REAL": float},
                "is_uncertain": bool
            }
        """
        if not self._loaded:
            self.load()

        clean_input = self.validate_input(news_text)
        processed = preprocess_text(clean_input)
        features = vectorize_text(processed, self._vec_bundle)

        raw_label = str(self._model.predict(features)[0])
        proba = self._model.predict_proba(features)[0]

        classes = [str(c) for c in self._model.classes_]
        prob_dict = {cls_name: float(round(float(p), 4)) for cls_name, p in zip(classes, proba)}
        confidence = float(round(float(max(proba)), 4))

        # Confidence thresholding: if confidence < 0.65, label as UNCERTAIN
        is_uncertain = confidence < CONFIDENCE_THRESHOLD
        effective_label = "UNCERTAIN" if is_uncertain else raw_label

        return {
            "label": effective_label,
            "prediction": effective_label,
            "raw_prediction": raw_label,
            "confidence": confidence,
            "probabilities": prob_dict,
            "is_uncertain": is_uncertain,
        }

    @property
    def is_ready(self) -> bool:
        """Returns True if model and vectorizers are loaded and ready."""
        return self._loaded


# Singleton instance
predictor = FakeNewsPredictor()
