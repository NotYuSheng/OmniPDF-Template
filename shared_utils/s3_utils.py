import os
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Optional

logger = logging.getLogger(__name__)

# Load from environment
S3_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")  # MinIO-compatible
S3_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
S3_BUCKET = os.getenv("MINIO_BUCKET", "omnifiles")
REGION_NAME = os.getenv("AWS_REGION", "ap-southeast-1")  # Optional; ignored by MinIO

# Instantiate boto3 S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=REGION_NAME
)

def upload_fileobj(file_obj, key: str, content_type: str = "application/pdf") -> bool:
    """
    Uploads a file-like object to S3.
    """
    try:
        s3_client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=S3_BUCKET,
            Key=key,
            ExtraArgs={"ContentType": content_type}
        )
        return True
    except (BotoCoreError, ClientError) as e:
        logger.exception(f"Failed to upload file to S3: {e}")
        return False

def generate_presigned_url(key: str, expiry_seconds: int = 300) -> Optional[str]:
    """
    Generates a presigned URL to download a file from S3.
    """
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=expiry_seconds
        )
    except (BotoCoreError, ClientError) as e:
        logger.exception(f"Failed to generate presigned URL: {e}")
        return None

def delete_file(key: str) -> bool:
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        logger.info(f"Deleted file with key: {key}")

        # Optional: verify deletion
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=key)
        still_exists = 'Contents' in response
        if still_exists:
            logger.warning(f"File still exists after deletion: {key}")
        return not still_exists

    except (BotoCoreError, ClientError) as e:
        logger.exception(f"Failed to delete file from S3: {e}")
        return False
