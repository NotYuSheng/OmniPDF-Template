FROM python:3.13-slim

WORKDIR /app

ENV PYTHONPATH=/app/cleaner_service

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt from cleaner_service folder in root context
COPY cleaner_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy utils folder from root context into /app/utils
COPY shared_utils ./cleaner_service/shared_utils

# Copy cleaner_service folder from root context into /app/cleaner_service
COPY cleaner_service ./cleaner_service

EXPOSE 8000

CMD ["sh", "-c", "python3 cleaner_service/main.py"]