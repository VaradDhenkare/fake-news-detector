"""
predictor.py  —  TruthLens ML Service
======================================
Singleton that loads trained model + vectorizer bundle at startup
and exposes a clean predict() interface used by app.py.

Vectorizer bundle format (saved by model_training.py):
    {
        "word": TfidfVectorizer  (word n-grams 1,2),
        "char": TfidfVectorizer  (char n-grams 3,5),
    }
Features are created by hstack(word_features, char_features).
"""

import os
import re
import string
import joblib
import numpy as np
import scipy.sparse
import nltk

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))

# ---------------------------------------------------------------------------
# Artifact paths
# ---------------------------------------------------------------------------
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH      = os.path.join(BASE_DIR, "artifacts", "model.joblib")
VECTORIZER_PATH = os.path.join(BASE_DIR, "artifacts", "vectorizer.joblib")


# ---------------------------------------------------------------------------
# Preprocessing  (must stay in sync with model_training.py)
# ---------------------------------------------------------------------------
def _preprocess(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation + string.digits))
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in STOP_WORDS and len(t) > 2]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Feature extraction helper
# ---------------------------------------------------------------------------
def _vectorize(text: str, vec_bundle) -> "scipy.sparse.csr_matrix":
    """
    Build feature matrix from text using the vectorizer bundle.
    Supports both:
      - New format: dict {"word": vec, "char": vec}  (dual TF-IDF)
      - Legacy format: single TfidfVectorizer
    """
    if isinstance(vec_bundle, dict):
        # New dual-vectorizer format
        word_feat = vec_bundle["word"].transform([text])
        char_feat = vec_bundle["char"].transform([text])
        return scipy.sparse.hstack([word_feat, char_feat], format="csr")
    else:
        # Legacy single-vectorizer format (backward compat)
        return vec_bundle.transform([text])


# ---------------------------------------------------------------------------
# Singleton Predictor
# ---------------------------------------------------------------------------
class FakeNewsPredictor:
    _instance   = None
    _model      = None
    _vec_bundle = None
    _loaded     = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self):
        """Load artifacts from disk — called once at startup."""
        if self._loaded:
            return

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Run: python model_training.py"
            )
        if not os.path.exists(VECTORIZER_PATH):
            raise FileNotFoundError(
                f"Vectorizer not found at {VECTORIZER_PATH}. Run: python model_training.py"
            )

        self._model      = joblib.load(MODEL_PATH)
        self._vec_bundle = joblib.load(VECTORIZER_PATH)
        self._loaded     = True
        print("[INFO] Model and vectorizer loaded successfully.")

    def predict(self, news_text: str) -> dict:
        """
        Return:
            {
                "prediction":    "FAKE" | "REAL",
                "confidence":    float,          # 0.0 – 1.0
                "probabilities": {"FAKE": float, "REAL": float}
            }
        """
        if not self._loaded:
            self.load()

        if not news_text or not news_text.strip():
            raise ValueError("news_text must be a non-empty string.")

        clean    = _preprocess(news_text)
        features = _vectorize(clean, self._vec_bundle)

        label  = self._model.predict(features)[0]
        proba  = self._model.predict_proba(features)[0]

        classes  = list(self._model.classes_)
        prob_dict = {cls: float(round(float(p), 4)) for cls, p in zip(classes, proba)}
        confidence = float(round(float(max(proba)), 4))

        return {
            "prediction":    label,
            "confidence":    confidence,
            "probabilities": prob_dict,
        }

    @property
    def is_ready(self) -> bool:
        return self._loaded


# ---------------------------------------------------------------------------
# Module-level singleton — imported by app.py
# ---------------------------------------------------------------------------
predictor = FakeNewsPredictor()
