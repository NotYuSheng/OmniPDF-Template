from fastapi import APIRouter, Depends, HTTPException, Response
import logging
from utils.redis import validate_session_doc_pair
from os import getenv
from httpx import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)
TABLE_PROCESSOR_URL = getenv("TABLE_PROCESSOR_URL")
if not TABLE_PROCESSOR_URL:
    raise ValueError("TABLE_PROCESSOR_URL is not set")


@router.get("/{doc_id}/tables")
async def get_pdf_tables(
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
        req = await client.get(f"{TABLE_PROCESSOR_URL}/{doc_id}")

        response.status_code = req.status_code
        return req.content
