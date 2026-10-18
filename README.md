# 🔍 TruthLens

TruthLens is a full-stack fake news detection platform that classifies news articles as Real, Fake, or Uncertain using machine learning. Users can analyze raw text, extract and score articles directly from web URLs, or monitor a real-time live news feed.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2.4-6DB33F?logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)

---

## ✨ Features

- **Text Analysis**: Paste any news excerpt to receive instant veracity classification with probability confidence.
- **URL Analysis**: Enter any news article link; the system scrapes the article body and evaluates credibility.
- **Live News Feed**: Automatically ingests top headlines from RSS feeds (BBC, Reuters, NPR, The Guardian) with live credibility scoring.
- **History & Bookmarks**: Paginated user history storing previous analyses with timestamps and source details.
- **JWT Authentication**: Secure user registration, login, and stateless token-based session management.
- **Health & Metrics**: Dedicated `/health` and `/metrics` observability endpoints tracking model precision, recall, and serving counts.

---

## 🛠️ Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6) | Responsive UI with real-time feedback, served via Nginx |
| **Backend API** | Java 17, Spring Boot 3.2.4 | REST API, Spring Security 6 (JWT), Spring Data JPA, WebClient |
| **ML Microservice** | Python 3.11, FastAPI, Uvicorn | Dual TF-IDF (word + char) + Calibrated LinearSVC classifier |
| **Database** | MySQL 8.0 | Relational storage for user accounts and prediction audit history |
| **DevOps** | Docker, Docker Compose | Multi-stage Docker builds and isolated bridge networking |

---

## 📁 Project Structure

```text
fake-news-detector/
├── frontend/             # HTML/CSS/JS client interface
├── backend/              # Spring Boot REST API & security
│   ├── src/              # Controllers, services, models, repositories
│   ├── pom.xml           # Maven dependencies
│   └── Dockerfile        # Multi-stage Java build
├── ml_service/           # FastAPI machine learning microservice
│   ├── app.py            # API routes and Pydantic schemas
│   ├── predictor.py      # Preprocessing and model inference
│   ├── model_training.py # Dual TF-IDF model training pipeline
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Python container image
├── docker-compose.yml    # Full-stack container orchestration
├── .env.example          # Environment variable template
└── README.md
```

---

## 🚀 Quick Start (Docker)

Run the entire application stack with a single command:

```bash
# 1. Clone repository and set up environment
git clone https://github.com/VaradDhenkare/fake-news-detector.git
cd fake-news-detector
cp .env.example .env

# 2. Build and start all services
docker compose up --build
```

### Access URLs:
- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Spring Boot Backend**: [http://localhost:8080](http://localhost:8080)
- **FastAPI Interactive Docs**: [http://localhost:5001/docs](http://localhost:5001/docs)
- **ML Health Check**: [http://localhost:5001/health](http://localhost:5001/health)

---

## 💻 Local Development

### 1. ML Microservice (Python)
```bash
cd ml_service
python -m venv venv
venv\Scripts\activate      # Windows (or source venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python model_training.py  # Generates model artifacts
python app.py             # Runs on http://localhost:5001
```

### 2. MySQL Database
Create a local database named `fakenews_db`:
```sql
CREATE DATABASE fakenews_db;
```

### 3. Java Backend (Spring Boot)
Set environment variables and launch the Spring Boot application:
```bash
cd backend
mvn clean package -DskipTests
java -jar target/fakenews-backend-1.0.0.jar  # Runs on http://localhost:8080
```

### 4. Frontend
Open `frontend/index.html` directly in your browser or serve it locally using any static web server.

---

## 📡 API Reference

### Health & Observability
```bash
# ML Microservice Health
curl http://localhost:5001/health

# MLOps Evaluation Metrics (Accuracy, Precision, Recall, F1)
curl http://localhost:5001/metrics

# Backend Aggregated Health (MySQL + ML Service)
curl http://localhost:8080/api/v1/health
```

### Predictions
```bash
# Text Prediction
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "The Senate passed a bipartisan infrastructure bill allocating funds for highways and transit."}'

# URL Prediction
curl -X POST http://localhost:5001/predict-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.bbc.com/news/world-us-canada-67890123"}'
```
