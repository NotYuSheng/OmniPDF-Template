from fastapi import APIRouter, Depends, HTTPException, Response
import logging
from utils.redis import validate_session_doc_pair
from os import getenv
from httpx import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{doc_id}/images")
async def get_pdf_images(
    doc_id: str,
    response: Response,
    valid_request: bool = Depends(validate_session_doc_pair),
):
    if not valid_request:
        raise HTTPException(status_code=403, detail="Failed to upload file to S3")
    async with AsyncClient() as client:
        req = await client.get(getenv("IMAGE_PROCESSOR_URL") + f"/{doc_id}")

        response.status_code = req.status_code
        return req.content
