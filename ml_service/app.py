"""
app.py  —  Fake News Detection ML Microservice
-----------------------------------------------
Flask REST API serving predictions from TF-IDF + Logistic Regression model.

Endpoints:
  GET  /health          → Service health check
  POST /predict         → Predict from raw text
  POST /predict-url     → Scrape URL and predict
  GET  /live-feed       → Fetch live RSS headlines and predict each

Run:
  python app.py
"""

import os
import logging
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from predictor import predictor
from news_fetcher import fetch_rss_articles, extract_article_text

# ── App init ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
SERVICE_START = time.time()


@app.before_request
def _ensure_model_loaded():
    if not predictor.is_ready:
        try:
            predictor.load()
        except FileNotFoundError as e:
            logger.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    """Service health check."""
    return jsonify({
        "status": "ok",
        "model_loaded": predictor.is_ready,
        "uptime_seconds": round(time.time() - SERVICE_START, 2),
        "service": "fake-news-detector-ml",
        "version": "2.0.0",
    }), 200


# ──────────────────────────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    """
    Predict from raw news text.

    Request: { "newsText": "..." }
    Response: { "prediction": "FAKE", "confidence": 0.85, "probabilities": {...} }
    """
    if not predictor.is_ready:
        return jsonify({"error": "Model not loaded. Run: python model_training.py"}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    news_text = data.get("newsText", "").strip()
    if not news_text:
        return jsonify({"error": "Missing field: 'newsText'"}), 400
    if len(news_text) < 10:
        return jsonify({"error": "'newsText' too short (min 10 characters)"}), 400

    try:
        result = predictor.predict(news_text)
        logger.info(f"predict() → {result['prediction']} ({result['confidence']:.2%})")
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        logger.exception("Error in /predict")
        return jsonify({"error": "Internal server error"}), 500


# ──────────────────────────────────────────────────────────────────────────────
@app.route("/predict-url", methods=["POST"])
def predict_url():
    """
    Scrape a news article URL and predict.

    Request:  { "url": "https://bbc.com/news/some-article" }
    Response: {
        "prediction":    "FAKE" | "REAL",
        "confidence":    0.87,
        "probabilities": {...},
        "title":         "Article headline",
        "url":           "https://...",
        "source":        "bbc.com",
        "text_snippet":  "First 200 chars of extracted text..."
    }

    cURL:
      curl -X POST http://localhost:5001/predict-url \\
           -H "Content-Type: application/json" \\
           -d '{"url":"https://www.bbc.com/news/world-us-canada-67890123"}'
    """
    if not predictor.is_ready:
        return jsonify({"error": "Model not loaded."}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing field: 'url'"}), 400

    try:
        # Step 1: Scrape article
        logger.info(f"Scraping URL: {url}")
        article = extract_article_text(url)

        # Step 2: Predict
        result = predictor.predict(article["text"])
        logger.info(f"predict-url() → {result['prediction']} ({result['confidence']:.2%}) [{url}]")

        return jsonify({
            **result,
            "title":        article["title"],
            "url":          article["url"],
            "source":       article["source"],
            "text_snippet": article["text"][:200] + "..." if len(article["text"]) > 200 else article["text"],
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        logger.exception("Error in /predict-url")
        return jsonify({"error": "Failed to analyze URL"}), 500


# ──────────────────────────────────────────────────────────────────────────────
@app.route("/live-feed", methods=["GET"])
def live_feed():
    """
    Fetch live headlines from RSS feeds and predict each article.

    Query params:
      max_per_source (int, default 5) — number of articles per RSS source

    Response: {
        "articles": [
            {
                "title":        "...",
                "summary":      "...",
                "url":          "...",
                "source":       "BBC News",
                "source_icon":  "🇬🇧",
                "published":    "...",
                "prediction":   "REAL",
                "confidence":   0.91,
                "probabilities":{"FAKE":0.09,"REAL":0.91}
            },
            ...
        ],
        "total": 25,
        "fetched_at": "2026-02-25T22:00:00"
    }
    """
    if not predictor.is_ready:
        return jsonify({"error": "Model not loaded."}), 503

    try:
        max_per = min(int(request.args.get("max_per_source", 5)), 10)
    except (ValueError, TypeError):
        max_per = 5

    try:
        logger.info(f"Fetching live RSS feed (max {max_per} per source)...")
        raw_articles = fetch_rss_articles(max_per_source=max_per)

        results = []
        for article in raw_articles:
            try:
                pred = predictor.predict(article["text"])
                results.append({
                    "title":        article["title"],
                    "summary":      article["summary"],
                    "url":          article["url"],
                    "source":       article["source"],
                    "source_icon":  article["source_icon"],
                    "published":    article["published"],
                    "prediction":   pred["prediction"],
                    "confidence":   pred["confidence"],
                    "probabilities":pred["probabilities"],
                    # Full text for the backend to store
                    "text":         article["text"],
                })
            except Exception as e:
                logger.warning(f"Skipping article (prediction error): {e}")
                continue

        logger.info(f"Live feed: {len(results)} articles predicted.")
        return jsonify({
            "articles":   results,
            "total":      len(results),
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }), 200

    except Exception:
        logger.exception("Error in /live-feed")
        return jsonify({"error": "Failed to fetch live news feed"}), 500


# ── Error Handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found. Available: GET /health, POST /predict, POST /predict-url, GET /live-feed"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed for this endpoint."}), 405


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5001))
    host  = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    logger.info("Pre-loading ML model artifacts...")
    try:
        predictor.load()
    except FileNotFoundError:
        logger.warning("⚠️  Model not found. Run 'python model_training.py' first.")

    logger.info(f"🚀 ML Service v2.0 starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
