import logging
from os import getenv
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from utils.asynchttp import proxy_post
from shared_utils.s3_utils import generate_presigned_url
from utils.session import validate_session_doc_pair
from shared_utils.s3_utils import load_job

router = APIRouter(prefix="/text-chunks", tags=["text-chunks"])
logger = logging.getLogger(__name__)
TEXT_CHUNK_PROCESSOR_URL = getenv("TEXT_CHUNK_PROCESSOR_URL")
if not TEXT_CHUNK_PROCESSOR_URL:
    raise ValueError("TEXT_CHUNK_PROCESSOR_URL is not set")


@router.get("/{doc_id}")
async def get_pdf_text_chunks(
    doc_id: str,
    valid_request: bool = Depends(validate_session_doc_pair),
):
    if not valid_request:
        raise HTTPException(
            status_code=403,
            detail="User not authorized to access this document or invalid document ID",
        )
    job = load_job(doc_id=doc_id, job_type="extraction")
    if not job:
        presign_url = generate_presigned_url(f"{doc_id}/original.pdf")
        param = {"doc_id": doc_id, "download_url": presign_url}
        return await proxy_post(f"{TEXT_CHUNK_PROCESSOR_URL}?{urlencode(param)}", body=None)
    
    if job.get("status") == "processing":
        raise HTTPException(
            status_code=202,
            detail="The document is still being processed. Please try again later."
        )

    try:
        return JSONResponse(content=job.get("data").get("result").get("texts"))
    except AttributeError as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="A Server Error has occured")
