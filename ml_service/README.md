# ML Service — Fake News Detector

A Flask microservice that detects fake news using **TF-IDF + Logistic Regression**.  
Designed to be called by a **Java Spring Boot** backend or any HTTP client.

---

## Project Structure

```
ml_service/
├── app.py               # Flask REST API (main entry point)
├── model_training.py    # Training pipeline
├── predictor.py         # Model singleton / prediction helper
├── download_dataset.py  # Dataset download/preparation helper
├── requirements.txt     # Python dependencies
├── data/
│   └── news.csv         # Training dataset (CSV: text, label)
└── artifacts/
    ├── model.joblib     # Trained Logistic Regression model
    └── vectorizer.joblib # Fitted TF-IDF vectorizer
```

---

## Setup & Run

### 1. Create Python virtual environment
```bash
cd ml_service
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download the dataset
**Option A — WELFake (auto-download, no login):**
```bash
python download_dataset.py --source welfake
```

**Option B — Kaggle dataset (manual download):**
1. Download from: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset
2. Place `Fake.csv` and `True.csv` in `ml_service/data/`
3. Run: `python download_dataset.py --source kaggle`

**Option C — Bring your own CSV:**
Place any CSV with `text` and `label` (FAKE/REAL) columns at `data/news.csv`.

### 4. Train the model
```bash
python model_training.py
```
Expected output:
```
[INFO] Loading dataset from: data/news.csv
[INFO] Dataset loaded: 72,134 samples
[INFO] Fitting TF-IDF vectorizer...
[INFO] Training Logistic Regression classifier...
Accuracy : 97.80%
✅ Training complete.
```

### 5. Start the Flask service
```bash
python app.py
```
Service runs on: `http://localhost:5001`

---

## API Reference

### `GET /health`
```bash
curl http://localhost:5001/health
```
```json
{
  "status": "ok",
  "model_loaded": true,
  "uptime_seconds": 5.2,
  "service": "fake-news-detector-ml",
  "version": "1.0.0"
}
```

---

### `POST /predict`

**cURL:**
```bash
curl -X POST http://localhost:5001/predict \
     -H "Content-Type: application/json" \
     -d '{"newsText": "Scientists discover water on Mars in major breakthrough"}'
```

**Postman:**
| Field  | Value                          |
|--------|--------------------------------|
| Method | POST                           |
| URL    | http://localhost:5001/predict  |
| Body   | raw → JSON                     |

```json
{
  "newsText": "Breaking: Government secretly planning to control minds via 5G towers"
}
```

**Response (200):**
```json
{
  "prediction": "FAKE",
  "confidence": 0.9432,
  "probabilities": {
    "FAKE": 0.9432,
    "REAL": 0.0568
  }
}
```

**Error responses:**
| HTTP | Reason |
|------|--------|
| 400  | Missing/empty `newsText` field |
| 400  | Text too short (< 10 chars) |
| 503  | Model not loaded — run `model_training.py` |

---

## Spring Boot Integration

Add a `RestTemplate` or `WebClient` call to your Java service:

```java
// application.properties
ml.service.url=http://localhost:5001

// FakeNewsClient.java
@Service
public class FakeNewsClient {

    @Value("${ml.service.url}")
    private String mlServiceUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public PredictionResult predict(String newsText) {
        Map<String, String> body = Map.of("newsText", newsText);
        return restTemplate.postForObject(
            mlServiceUrl + "/predict",
            body,
            PredictionResult.class
        );
    }
}
```

---

## Notes

- Model is loaded **once at startup** (not per-request) for performance.
- TF-IDF uses **unigrams + bigrams** (`ngram_range=(1,2)`) with 50k vocabulary.
- Logistic Regression chosen over Naive Bayes for **better probability calibration**.
- To retrain with new data, replace `data/news.csv` and re-run `model_training.py`.
