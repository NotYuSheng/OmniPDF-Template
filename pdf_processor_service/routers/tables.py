import logging
from os import getenv

from fastapi import APIRouter, Depends, HTTPException, Response

from models.tables import TablesResponse
from utils.asynchttp import proxy_get, proxy_post
from shared_utils.s3_utils import generate_presigned_url
from utils.session import validate_session_doc_pair
from shared_utils.redis import get_set_storage, RedisSetStorage

router = APIRouter(prefix="/tables", tags=["tables"])
logger = logging.getLogger(__name__)
TABLE_PROCESSOR_URL = getenv("TABLE_PROCESSOR_URL")
if not TABLE_PROCESSOR_URL:
    raise ValueError("TABLE_PROCESSOR_URL is not set")


@router.get("/{doc_id}", response_model=TablesResponse)
async def get_pdf_tables(
    doc_id: str,
    response: Response,
    valid_request: bool = Depends(validate_session_doc_pair),
    service_cache: RedisSetStorage = Depends(get_set_storage),
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
            f"{TABLE_PROCESSOR_URL}",
            body={"doc_id": doc_id, "download_url": download_url},
        )
    else:
        req = await proxy_get(f"{TABLE_PROCESSOR_URL}/{doc_id}")
    if req.status_code == 202 and not doc_is_processing:
        service_cache.append(__name__, doc_id)
    elif req.status_code == 200 and doc_is_processing:
        service_cache.remove(__name__, doc_id)
    response.status_code = req.status_code
    return req.json()
