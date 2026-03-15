"""Quick diagnostic — checks why model always predicts FAKE."""
import joblib, scipy.sparse, pandas as pd, os, re, string
import nltk; nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))
BASE = os.path.dirname(os.path.abspath(__file__))

def preprocess(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation + string.digits))
    text = re.sub(r"\s+", " ", text).strip()
    return " ".join(t for t in text.split() if t not in STOP_WORDS and len(t) > 2)

model   = joblib.load(os.path.join(BASE, "artifacts", "model.joblib"))
vec_b   = joblib.load(os.path.join(BASE, "artifacts", "vectorizer.joblib"))

print("=== Model classes:", model.classes_)

def predict(text):
    clean = preprocess(text)
    if isinstance(vec_b, dict):
        feat = scipy.sparse.hstack([vec_b["word"].transform([clean]),
                                    vec_b["char"].transform([clean])], format="csr")
    else:
        feat = vec_b.transform([clean])
    proba = model.predict_proba(feat)[0]
    label = model.predict(feat)[0]
    classes = list(model.classes_)
    return label, {c: round(float(p), 3) for c, p in zip(classes, proba)}

# Test known REAL sentences
real_tests = [
    "The Federal Reserve raised interest rates by 25 basis points today.",
    "Scientists at NASA discovered a new exoplanet orbiting a distant star.",
    "Apple reported record quarterly earnings of 90 billion dollars yesterday.",
    "The Prime Minister signed a new climate agreement at the UN summit.",
]

# Test known FAKE sentences
fake_tests = [
    "Drinking bleach cures COVID-19, doctors confirm, government hiding truth.",
    "Obama born in Kenya: secret documents prove birth certificate was fake.",
    "5G towers spread coronavirus, scientists find microchips in vaccines.",
]

print("\n--- Legitimate news (should be REAL) ---")
for t in real_tests:
    label, proba = predict(t)
    print(f"  [{label}] ({proba}) :: {t[:60]}...")

print("\n--- Fake news (should be FAKE) ---")
for t in fake_tests:
    label, proba = predict(t)
    print(f"  [{label}] ({proba}) :: {t[:60]}...")

# Check dataset label distribution
df = pd.read_csv(os.path.join(BASE, "data", "news.csv"))
print(f"\n--- Dataset: {len(df)} rows ---")
print(df["label"].value_counts())
print("\nSample REAL text (first 200 chars):")
print(df[df["label"]=="REAL"]["text"].iloc[0][:200])
print("\nSample FAKE text (first 200 chars):")
print(df[df["label"]=="FAKE"]["text"].iloc[0][:200])
