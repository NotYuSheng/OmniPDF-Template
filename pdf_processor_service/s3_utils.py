import os
from minio import Minio
from datetime import timedelta
from dotenv import load_dotenv

# Optional: Load from .env file if used
load_dotenv()

# Load credentials and config from environment
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Initialize MinIO client
client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

def generate_presigned_url(bucket: str, object_name: str, expiry_seconds: int = 300) -> str:
    return client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=timedelta(seconds=expiry_seconds),
    )

def upload_file(bucket: str, object_name: str, file_data: bytes, content_type: str):
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=file_data,
        length=len(file_data),
        content_type=content_type,
    )
