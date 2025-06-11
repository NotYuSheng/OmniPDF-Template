from minio import Minio
from datetime import timedelta

client = Minio(
    endpoint="minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
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
