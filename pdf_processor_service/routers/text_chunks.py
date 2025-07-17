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
EXTRACTION_URL = getenv("EXTRACTION_URL")
if not EXTRACTION_URL:
    raise ValueError("EXTRACTION_URL is not set")


@router.get("/{doc_id}")
async def get_pdf_text_chunks(
    doc_id: str,
    valid_request: bool = Depends(validate_session_doc_pair),
):
    job = load_job(doc_id=doc_id, job_type="extraction")
    if not job:
        presign_url = generate_presigned_url(f"{doc_id}/original.pdf")
        param = {"doc_id": doc_id, "download_url": presign_url}
        return await proxy_post(f"{EXTRACTION_URL}?{urlencode(param)}", body=None)
    
    if job.get("status") == "processing":
        raise HTTPException(
            status_code=202,
            detail="The document is still being processed. Please try again later."
        )

    texts = job.get("data", {}).get("result", {}).get("texts")
    if texts is None:
        logger.error(f"Could not find 'texts' in job result for doc_id: {doc_id}")
        raise HTTPException(status_code=500, detail="A server error has occurred.")
    return JSONResponse(content=texts)
