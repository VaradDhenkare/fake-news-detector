"""
download_dataset.py  —  TruthLens ML Service
=============================================

Downloads the ISOT Fake News Dataset (~38 MB zip) which contains:
  - ~23,000 FAKE news articles
  - ~21,000 REAL news articles
  - Total: ~44,000 samples  →  achieves 97-99% accuracy after training

Compared to WELFake (245 MB), this is 6× smaller and downloads much faster.

Source: University of Victoria (ISOT Research Lab)
  https://onlineacademiccommunity.uvic.ca/isot/

Usage:
    python download_dataset.py
"""

import os
import zipfile
import urllib.request
import urllib.error
import io
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
OUT_PATH  = os.path.join(DATA_DIR, "news.csv")

# ---------------------------------------------------------------------------
# ISOT Dataset  — ~38 MB zip  (Fake.csv + True.csv inside)
# ---------------------------------------------------------------------------
ISOT_ZIP_URL = (
    "https://onlineacademiccommunity.uvic.ca/isot/wp-content/uploads/"
    "sites/7/2023/02/News-_dataset.zip"
)

# Fallback: single-file ~5 MB CSV (6,335 samples → ~93-95% accuracy)
FALLBACK_URL = (
    "https://raw.githubusercontent.com/joolsa/"
    "fake_real_news_dataset/master/fake_or_real_news.csv.zip"
)


# ---------------------------------------------------------------------------
# Progress hook
# ---------------------------------------------------------------------------
def _progress(count, block_size, total_size):
    if total_size > 0:
        pct = min(100, count * block_size * 100 // total_size)
        mb_done  = count * block_size / 1_048_576
        mb_total = total_size / 1_048_576
        print(f"\r  Downloading … {pct:3d}%  ({mb_done:.1f} / {mb_total:.1f} MB)", end="", flush=True)


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------
def _download_bytes(url: str) -> bytes:
    """Download URL to memory with retry and progress."""
    print(f"[INFO] Downloading: {url}")
    for attempt in range(1, 4):
        try:
            tmp, _ = urllib.request.urlretrieve(url, reporthook=_progress)
            print()  # newline after progress
            with open(tmp, "rb") as f:
                data = f.read()
            os.unlink(tmp)
            return data
        except urllib.error.ContentTooShortError:
            print(f"\n[WARN] Incomplete download on attempt {attempt}/3 — retrying…")
        except Exception as e:
            print(f"\n[WARN] Attempt {attempt} failed: {e}")
    raise RuntimeError("All download attempts failed.")


# ---------------------------------------------------------------------------
# Build news.csv from ISOT zip  (Fake.csv + True.csv)
# ---------------------------------------------------------------------------
def _process_isot_zip(data: bytes) -> pd.DataFrame:
    """Extract Fake.csv + True.csv from the ISOT zip, combine, return DataFrame."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        print(f"[INFO] Zip contents: {names}")

        # Look for Fake / True csv files (may be in a subdirectory)
        fake_name = next((n for n in names if "fake" in n.lower() and n.endswith(".csv")), None)
        true_name = next((n for n in names if "true" in n.lower() and n.endswith(".csv")), None)

        if fake_name is None or true_name is None:
            raise ValueError(f"Expected Fake.csv + True.csv inside zip. Found: {names}")

        df_fake = pd.read_csv(io.BytesIO(z.read(fake_name)), on_bad_lines="skip")
        df_true = pd.read_csv(io.BytesIO(z.read(true_name)), on_bad_lines="skip")

    df_fake["label"] = "FAKE"
    df_true["label"] = "REAL"
    df = pd.concat([df_fake, df_true], ignore_index=True)
    return df


# ---------------------------------------------------------------------------
# Build news.csv from flat fake_or_real_news.csv fallback
# ---------------------------------------------------------------------------
def _process_fallback_zip(data: bytes) -> pd.DataFrame:
    """Extract fake_or_real_news.csv from zip."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        csv_name = next((n for n in z.namelist() if n.endswith(".csv")), None)
        if csv_name is None:
            raise ValueError("No CSV found in fallback zip.")
        raw = pd.read_csv(io.BytesIO(z.read(csv_name)), on_bad_lines="skip")

    raw.columns = [c.strip().lower() for c in raw.columns]
    # label column is 'label' with values FAKE / REAL
    raw["label"] = raw["label"].str.upper().str.strip()
    return raw


# ---------------------------------------------------------------------------
# Normalise → news.csv  (columns: text, label)
# ---------------------------------------------------------------------------
def _to_news_csv(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]

    # Combine title + text if both present
    if "title" in df.columns and "text" in df.columns:
        df["text"] = df["title"].fillna("") + " " + df["text"].fillna("")
    elif "title" in df.columns:
        df["text"] = df["title"].fillna("")
    elif "text" not in df.columns:
        raise ValueError("No usable text column found.")

    df["label"] = df["label"].str.upper().str.strip()
    df = df[["text", "label"]].dropna()
    df = df[df["label"].isin(["FAKE", "REAL"])].copy()
    df = df[df["text"].str.len() > 20].copy()   # drop trivially short rows
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def download():
    os.makedirs(DATA_DIR, exist_ok=True)

    df = None

    # ── Attempt 1: ISOT zip (~38 MB, 44 K samples) ─────────────────────────
    print("\n=== Attempting ISOT News Dataset (~38 MB, 44,000 samples) ===")
    try:
        data = _download_bytes(ISOT_ZIP_URL)
        df   = _process_isot_zip(data)
        print(f"[INFO] ISOT download successful: {len(df):,} raw rows")
    except Exception as e:
        print(f"[WARN] ISOT download failed: {e}")

    # ── Attempt 2: Fallback single-file (~5 MB, 6 K samples) ───────────────
    if df is None:
        print("\n=== Falling back to fake_or_real_news.csv (~5 MB, 6,335 samples) ===")
        try:
            data = _download_bytes(FALLBACK_URL)
            df   = _process_fallback_zip(data)
            print(f"[INFO] Fallback download successful: {len(df):,} raw rows")
        except Exception as e:
            print(f"[WARN] Fallback download also failed: {e}")

    # ── Attempt 3: Use existing synthetic dataset if already present ────────
    if df is None:
        if os.path.exists(OUT_PATH):
            print(f"\n[INFO] Using existing dataset at: {OUT_PATH}")
            print("       Run 'python create_sample_dataset.py' to regenerate if needed.")
            return
        else:
            print("\n[ERROR] All downloads failed. Generating a small synthetic dataset instead.")
            print("        Run: python create_sample_dataset.py")
            raise RuntimeError(
                "Cannot download dataset and no local dataset exists. "
                "Run: python create_sample_dataset.py"
            )

    # ── Normalise and save ──────────────────────────────────────────────────
    df = _to_news_csv(df)
    df.to_csv(OUT_PATH, index=False)
    print(f"\n[INFO] Dataset saved → {OUT_PATH}")
    print(f"[INFO] Total samples  : {len(df):,}")
    print(f"[INFO] FAKE           : {(df['label'] == 'FAKE').sum():,}")
    print(f"[INFO] REAL           : {(df['label'] == 'REAL').sum():,}")
    print("\n✅ Ready!  Next step → python model_training.py")


if __name__ == "__main__":
    download()
