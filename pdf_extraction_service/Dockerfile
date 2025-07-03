# FROM python:3.13-slim
FROM registry.connect.redhat.com/nvidia/gpu-operator-bundle


WORKDIR /app

ENV PYTHONPATH=/app/pdf_extraction_service:/app/shared_utils

# Install Python and build tools
RUN dnf install -y python3 python3-pip gcc gcc-c++ make && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    dnf clean all

# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
# RUN microdnf install -y gcc gcc-c++ make && microdnf clean all

COPY pdf_extraction_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY shared_utils ./shared_utils

COPY pdf_extraction_service ./pdf_extraction_service

EXPOSE 8000

# Start the FastAPI server
CMD ["sh", "-c", "PYTHONPATH=/app/pdf_extraction_service uvicorn pdf_extraction_service.main:app --host 0.0.0.0 --port 8000"]