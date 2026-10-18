FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for networking and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache NLTK stopwords into the container image
RUN python -c "import nltk; nltk.download('stopwords', quiet=True)"

COPY . .

EXPOSE 5001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
