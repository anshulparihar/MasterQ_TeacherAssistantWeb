FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for PostgreSQL and building Python packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    libcairo2 \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
