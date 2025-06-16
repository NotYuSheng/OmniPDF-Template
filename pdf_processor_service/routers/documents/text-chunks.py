from fastapi import APIRouter, Depends, HTTPException, Response
import logging
from utils.redis import validate_session_doc_pair
from os import getenv
from httpx import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{doc_id}/text-chunks")
async def get_pdf_text_chunks(
    doc_id: str,
    response: Response,
    valid_request: bool = Depends(validate_session_doc_pair),
):
    if not valid_request:
        raise HTTPException(status_code=403, detail="Not Authorised to access file")
    async with AsyncClient() as client:
        req = await client.get(getenv("IMAGE_PROCESSER_URL") + f"/{doc_id}")

        response.status_code = req.status_code
        return req.content
