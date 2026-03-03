FROM python:3.11-slim
 
WORKDIR /app
 
# Install system dependencies for compiling psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
# Ensure static and uploads directory exists and is owned by appuser
RUN mkdir -p static/uploads && chown -R appuser:appuser /app
 
USER appuser
 
EXPOSE 8000
 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
