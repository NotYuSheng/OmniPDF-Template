from fastapi import APIRouter, Depends, HTTPException, Response
import logging
from utils.redis import validate_session_doc_pair
import requests
from os import getenv

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{doc_id}/images")
async def get_pdf_images(
    doc_id: str,
    valid_request: bool = Depends(validate_session_doc_pair),
    response=Response,
):
    if not valid_request:
        raise HTTPException(status_code=403, detail="Failed to upload file to S3")
    req = requests.get(getenv("IMAGE_PROCESSER_URL") + f"/{doc_id}")

    response.status_code = req.status_code
    return req.content
