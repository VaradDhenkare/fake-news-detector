# Backend — Fake News Detector (Spring Boot)

Java Spring Boot REST API with JWT authentication, MySQL persistence, and integration with the Python ML microservice.

---

## Project Structure

```
backend/
├── pom.xml
└── src/main/java/com/fakenews/backend/
    ├── FakeNewsApplication.java
    ├── controller/
    │   ├── AuthController.java       # /api/auth/**
    │   └── NewsController.java       # /api/news/**
    ├── service/
    │   ├── AuthService.java          # Register + JWT login
    │   ├── NewsAnalysisService.java  # predict + history
    │   └── MlClientService.java      # WebClient → Flask ML
    ├── repository/
    │   ├── UserRepository.java
    │   └── NewsAnalysisRepository.java
    ├── model/
    │   ├── User.java
    │   └── NewsAnalysis.java
    ├── dto/
    │   ├── RegisterRequest.java
    │   ├── LoginRequest.java
    │   ├── AuthResponse.java
    │   ├── PredictRequest.java
    │   ├── MlPredictionResponse.java
    │   └── NewsAnalysisResponse.java
    ├── security/
    │   ├── SecurityConfig.java
    │   ├── JwtUtils.java
    │   ├── JwtAuthFilter.java
    │   └── UserDetailsServiceImpl.java
    └── exception/
        ├── GlobalExceptionHandler.java
        ├── ResourceNotFoundException.java
        ├── ConflictException.java
        └── MlServiceException.java
```

---

## Prerequisites

- Java 17+
- Maven 3.8+
- MySQL 8.x running locally
- Python ML service running on port **5001**

---

## Setup

### 1. Create MySQL database
```sql
CREATE DATABASE fakenews_db;
```

### 2. Configure `application.properties`
Edit `src/main/resources/application.properties`:
```properties
spring.datasource.username=root
spring.datasource.password=YOUR_PASSWORD
```

### 3. Build & Run
```bash
cd backend
mvn clean install
mvn spring-boot:run
```
Server starts on: `http://localhost:8080`

---

## API Reference

### Auth — Public Endpoints

#### `POST /api/auth/register`
```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@test.com","password":"secret123"}'
```
```json
{ "message": "User registered successfully!" }
```

#### `POST /api/auth/login`
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"secret123"}'
```
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "tokenType": "Bearer",
  "username": "john",
  "role": "USER"
}
```

---

### News — Protected Endpoints (JWT Required)

Use header: `Authorization: Bearer <token>`

#### `POST /api/news/predict`
```bash
curl -X POST http://localhost:8080/api/news/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"newsText":"Scientists find cure for diabetes in major breakthrough"}'
```
```json
{
  "id": 1,
  "newsText": "Scientists find cure...",
  "prediction": "REAL",
  "confidence": 0.87,
  "createdAt": "2026-02-25T19:00:00",
  "username": "john"
}
```

#### `GET /api/news/history?page=0&size=10`
```bash
curl http://localhost:8080/api/news/history \
  -H "Authorization: Bearer <token>"
```

#### `DELETE /api/news/history/{id}`
```bash
curl -X DELETE http://localhost:8080/api/news/history/1 \
  -H "Authorization: Bearer <token>"
```

---

## How Backend communicates with ML Service

```
Frontend  →  POST /api/news/predict (Spring Boot)
                │
                ▼  (WebClient: HTTP POST with JSON)
         Python Flask ML Service (localhost:5001/predict)
                │
                ▼  (JSON response)
         { "prediction": "FAKE", "confidence": 0.93 }
                │
                ▼  (Stored in MySQL → returned to frontend)
         NewsAnalysis saved to news_analyses table
```

- **WebClient** (reactive, non-blocking) is used instead of RestTemplate
- Configurable via `ml.service.base-url` and `ml.service.timeout-seconds`
- If Flask is down, the API returns HTTP 502 with a clear error message
