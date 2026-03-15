# 🔍 TruthLens — Fake News Detector

A web application that uses Machine Learning to detect fake news articles. You can **paste text**, **enter a URL**, or browse a **Live News Feed** — the app tells you if the news is likely **REAL** or **FAKE**.

---

## 📁 Project Structure

```
Fake-news-detector/
├── frontend/          → HTML/CSS/JS UI (open index.html in browser)
├── backend/           → Java Spring Boot REST API (port 8080)
├── ml_service/        → Python Flask ML service (port 5001)
├── .env.example       → Template for environment variables
└── .gitignore
```

---

## ✅ What You Need Installed

- **Python** 3.9+ → [Download](https://www.python.org/downloads/)
- **Java JDK** 17+ → [Download](https://adoptium.net/)
- **Maven** 3.8+ → [Download](https://maven.apache.org/download.cgi)
- **MySQL** 8.x → [Download](https://dev.mysql.com/downloads/mysql/)

---

## 🚀 How to Run

### 1. Set Up the ML Service (Python)

```bash
cd ml_service

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows CMD
# venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate   # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Download dataset and train the model
python download_dataset.py --source welfake
python model_training.py

# Start the ML service
python app.py
```

### 2. Set Up MySQL

```sql
CREATE DATABASE fakenews_db;
```

### 3. Configure & Run the Backend (Java)

First, set environment variables for your database credentials:

```powershell
# Windows PowerShell
$env:DB_PASSWORD="your_mysql_password"
$env:JWT_SECRET="any_long_random_string_here"
```
```bash
# Linux / macOS
export DB_PASSWORD="your_mysql_password"
export JWT_SECRET="any_long_random_string_here"
```

Then run:
```bash
cd backend
mvn clean install -DskipTests
mvn spring-boot:run
```

### 4. Open the Frontend

Just open `frontend/index.html` in your browser — no build step needed.

---

## 🎯 How to Use

| Feature | How |
|---------|-----|
| **Analyze Text** | Paste news text → click **Verify Article** |
| **Analyze URL** | Paste a news article URL → click **Analyze URL** |
| **Live Feed** | Click **🔄 Refresh Feed** to fetch real headlines from BBC, Reuters, etc. |
| **History** | View all your past analyses, delete any entry |

---

## 📋 Start Order (Every Session)

```
1. Start MySQL
2. python ml_service/app.py          → runs on port 5001
3. cd backend && mvn spring-boot:run → runs on port 8080
4. Open frontend/index.html in browser
```

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `Model not found` | Run `python model_training.py` first |
| MySQL connection refused | Check MySQL is running and your `DB_PASSWORD` env variable is correct |
| Frontend shows errors | Make sure both the ML service and backend are running |
| URL analysis times out | Some sites block scraping — try pasting the text instead |

---

*TruthLens — Verify before you share.* ✨
