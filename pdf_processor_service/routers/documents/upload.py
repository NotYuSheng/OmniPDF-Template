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
S3_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

# Set up the S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    doc_id = str(uuid.uuid4())
    key = f"{doc_id}.pdf"

    try:
        # Upload file to MinIO
        s3_client.upload_fileobj(file.file, S3_BUCKET, key)

        # Generate a presigned download URL (valid for 5 minutes)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=300  # 5 minutes
        )

    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"Upload or URL generation failed: {str(e)}")

    return JSONResponse(content={
        "doc_id": doc_id,
        "filename": file.filename,
        "download_url": presigned_url
    })
