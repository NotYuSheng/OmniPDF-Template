from fastapi import APIRouter, Depends, HTTPException, Response
import logging
from utils.redis import validate_session_doc_pair
from os import getenv
from httpx import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)
IMAGE_PROCESSOR_URL = getenv("IMAGE_PROCESSOR_URL")
if not IMAGE_PROCESSOR_URL:
    raise ValueError("IMAGE_PROCESSOR_URL is not set")


@router.get("/{doc_id}/images")
async def get_pdf_images(
    doc_id: str,
    response: Response,
    valid_request: bool = Depends(validate_session_doc_pair),
):
    if not valid_request:
        raise HTTPException(
            status_code=403,
            detail="User not authorized to access this document or invalid document ID",
        )
    async with AsyncClient() as client:
        req = await client.get(getenv("IMAGE_PROCESSOR_URL") + f"/{doc_id}")

        response.status_code = req.status_code
        return req.content
