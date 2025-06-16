from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
import logging
from s3_utils import get_file
from utils.redis import validate_session_doc_pair
from tempfile import TemporaryFile
from os import getenv
from httpx import AsyncClient

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_pdf_tables_from_s3(
    doc_id: str, valid_request: bool = Depends(validate_session_doc_pair)
):
    if not valid_request:
        raise HTTPException(status_code=403, detail="Not Authorised to access file")

    with TemporaryFile() as f:
        get_file(f"{doc_id}_tables.csv", f)
        f.seek(0)
        return StreamingResponse(content=f, media_type="text/csv")


@router.get("/{doc_id}/tables")
async def get_pdf_tables(
    doc_id: str,
    response: Response,
    valid_request: bool = Depends(validate_session_doc_pair),
):
    if not valid_request:
        raise HTTPException(status_code=403, detail="Not Authorised to access file")
    async with AsyncClient() as client:
        req = await client.get(getenv("IMAGE_PROCESSOR_URL") + f"/{doc_id}")

        response.status_code = req.status_code
        return req.content
