from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uuid
import logging
from s3_utils import upload_fileobj, generate_presigned_url
from models.document import DocumentUploadResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File extension must be .pdf")

    # Check file header for actual PDF content
    header = await file.read(4)
    if header != b"%PDF":
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF (header mismatch)")
    await file.seek(0)  # Rewind for upload

    # Generate a UUID for this document
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
        filename=file.filename,
        download_url=presigned_url
    )
