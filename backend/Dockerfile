FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 if needed (slim might need build-essential/libpq-dev)
# But psycopg2-binary usually handles this. Adding just in case.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure static and uploads directory exists
RUN mkdir -p static/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
