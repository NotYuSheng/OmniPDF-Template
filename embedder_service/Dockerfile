FROM python:3.13-slim

WORKDIR /app

ENV PYTHONPATH=/app/embedder_service:/app/shared_utils

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from embedder_service folder in root context
COPY embedder_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy utils folder from root context into /app/utils
COPY shared_utils ./shared_utils

# Copy embedder_service folder from root context into /app/embedder_service
COPY embedder_service ./embedder_service

EXPOSE 8000

CMD ["sh", "-c", "PYTHONPATH=/app/embedder_service uvicorn embedder_service.main:app --host 0.0.0.0 --port 8000"]