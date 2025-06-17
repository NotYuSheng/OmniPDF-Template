from fastapi import APIRouter, File, UploadFile, HTTPException
import uuid
import logging
from shared_utils.s3_utils import upload_fileobj, generate_presigned_url, delete_file, s3_client, S3_BUCKET
from models.document import DocumentUploadResponse
from botocore.exceptions import ClientError

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File extension must be .pdf")

    header = await file.read(4)
    if header != b"%PDF":
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF (header mismatch)")
    await file.seek(0)

    doc_id = str(uuid.uuid4())
    key = f"{doc_id}.pdf"

    try:
        success = upload_fileobj(file.file, key, content_type=file.content_type or "application/pdf")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")

        presigned_url = generate_presigned_url(key)
        if not presigned_url:
            raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=key,
        download_url=presigned_url
    )

@router.get("/{doc_id}", response_model=DocumentUploadResponse)
async def get_document(doc_id: str):
    key = f"{doc_id}.pdf"

    # Check if object exists
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=key)
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            raise HTTPException(status_code=404, detail="Document not found")
        raise HTTPException(status_code=500, detail="Failed to check document")

    presigned_url = generate_presigned_url(key)
    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=key,
        download_url=presigned_url
    )

@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str):
    key = f"{doc_id}.pdf"
    if success:
        logger.info(f"Successfully deleted document: {key}")
    else:
        logger.warning(f"Document not found or could not be deleted: {key}")
        raise HTTPException(status_code=404, detail="Document not found")
