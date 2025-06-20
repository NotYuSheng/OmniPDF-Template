import logging
from os import getenv

from fastapi import APIRouter, Depends, HTTPException, Response

from models.text_chunks import TextChunksResponse
from utils.asynchttp import proxy_get, proxy_post
from shared_utils.s3_utils import generate_presigned_url
from shared_utils.redis import get_service_cache, validate_session_doc_pair, ServiceCache

router = APIRouter(prefix="/text-chunks", tags=["text-chunks"])
logger = logging.getLogger(__name__)
TEXT_CHUNK_PROCESSOR_URL = getenv("TEXT_CHUNK_PROCESSOR_URL")
if not TEXT_CHUNK_PROCESSOR_URL:
    raise ValueError("TEXT_CHUNK_PROCESSOR_URL is not set")

incomplete_jobs = []

@router.get("/{doc_id}", response_model=TextChunksResponse)
async def get_pdf_text_chunks(
    doc_id: str,
    response: Response,
    valid_request: bool = Depends(validate_session_doc_pair),
    service_cache: ServiceCache = Depends(get_service_cache),
):
    if not valid_request:
        raise HTTPException(
            status_code=403,
            detail="User not authorized to access this document or invalid document ID",
        )
    doc_is_processing = service_cache.contains(__name__, doc_id)
    if not doc_is_processing:
        download_url = generate_presigned_url(f"{doc_id}.pdf")
        req = await proxy_post(
            f"{TEXT_CHUNK_PROCESSOR_URL}",
            body={"doc_id": doc_id, "download_url": download_url},
        )
    else:
        req = await proxy_get(f"{TEXT_CHUNK_PROCESSOR_URL}/{doc_id}")
    if req.status_code == 202 and not doc_is_processing:
        service_cache.add(doc_id)
    elif req.status_code == 200 and doc_is_processing:
        service_cache.remove(doc_id)
    response.status_code = req.status_code
    return req.content
