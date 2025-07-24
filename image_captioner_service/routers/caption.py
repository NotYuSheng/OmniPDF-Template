from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging
import requests
import time
import io
import json

from models.caption import ImageCaptioningResponse
from shared_utils.s3_utils import (
    save_job, 
    load_job,
    upload_fileobj,
)

router = APIRouter(prefix="/caption", tags=["caption"])
logger = logging.getLogger(__name__)

@router.post("/caption", response_model=ImageCaptioningResponse, status_code=202)
async def process_pdf(doc_id: str, 
                      image_id: str, 
                      image_url: str, 
                      prompt: str
                      ):
    response = requests.get(image_url)
    response.raise_for_status()
    logger.info(f"Image fetch status: {response.status_code}")
    logger.info(f"Content-Type: {response.headers.get('Content-Type')}")
    logger.info(f"Image size: {len(response.content)} bytes")

    return ImageCaptioningResponse(doc_id=doc_id, image_id=image_id, caption="True")
