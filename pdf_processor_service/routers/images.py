import logging
from os import getenv

import os
import io
import boto3

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from models.images import ImageResponse
from utils.asynchttp import proxy_get, proxy_post
from shared_utils.s3_utils import generate_presigned_url, get_file
from shared_utils.redis import (
    get_service_cache,
    validate_session_doc_pair,
    ServiceCache,
)


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


router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)
IMAGE_PROCESSOR_URL = getenv("IMAGE_PROCESSOR_URL")
if not IMAGE_PROCESSOR_URL:
    raise ValueError("IMAGE_PROCESSOR_URL is not set")


@router.get("/{doc_id}")
async def get_pdf_images(
        doc_id: str,
        response: Response,
        valid_request: bool = Depends(validate_session_doc_pair),
        service_cache: ServiceCache = Depends(get_service_cache),
    ):

    url_list = []

    if not valid_request:
        raise HTTPException(
            status_code=403,
            detail="User not authorized to access this document or invalid document ID",
        )
    doc_is_processing = service_cache.contains(__name__, doc_id)
    if not doc_is_processing:
        prefix = f"{doc_id}/images/"
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        keys = [obj["Key"] for obj in response.get("Contents", [])]
        
        for i in keys:
            url = generate_presigned_url(i)
            url_list.append(url)
    
    return url_list