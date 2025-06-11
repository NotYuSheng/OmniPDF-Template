from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uuid
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import os

router = APIRouter()

# MinIO (S3-compatible) configuration from environment
S3_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
S3_BUCKET = os.getenv("MINIO_BUCKET", "omnifiles")
S3_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# Set up the S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Generate a UUID as document ID
    doc_id = str(uuid.uuid4())
    key = f"{doc_id}.pdf"

    try:
        # Upload file to MinIO
        s3_client.upload_fileobj(file.file, S3_BUCKET, key)
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail="Failed to upload file")

    return JSONResponse(content={"doc_id": doc_id, "filename": file.filename})
