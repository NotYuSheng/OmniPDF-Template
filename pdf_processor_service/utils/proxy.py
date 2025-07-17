import os

S3_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")  # MinIO-compatible
EXTERNAL_S3_ENDPOINT = os.getenv("EXTERNAL_S3_ENDPOINT")
if not EXTERNAL_S3_ENDPOINT:
    raise ValueError("EXTERNAL_S3_ENDPOINT is not set")

def get_external_minio_uri(uri: str):
    new_uri = uri.replace(S3_ENDPOINT, EXTERNAL_S3_ENDPOINT)
    return new_uri
