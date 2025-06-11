import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from datetime import timedelta

# Optional: Load from .env file
load_dotenv()

# Load environment variables
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")  # MinIO for dev
S3_BUCKET = os.getenv("S3_BUCKET", "omnifiles")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")

# Setup S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

def upload_file(bucket: str, object_name: str, file_data: bytes, content_type: str):
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=file_data,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 upload failed: {str(e)}")

def generate_presigned_url(bucket: str, object_name: str, expiry_seconds: int = 300) -> str:
    try:
        return s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': object_name},
            ExpiresIn=expiry_seconds
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Presigned URL generation failed: {str(e)}")
