import logging
from os import getenv

from models.images import ImageResponse, ImageData
from fastapi import APIRouter, Depends, HTTPException
from shared_utils.s3_utils import generate_presigned_url, s3_client, S3_BUCKET, load_job
from shared_utils.redis import validate_session_doc_pair

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)
IMAGE_PROCESSOR_URL = getenv("IMAGE_PROCESSOR_URL")
if not IMAGE_PROCESSOR_URL:
    raise ValueError("IMAGE_PROCESSOR_URL is not set")


@router.get("/{doc_id}")
async def get_pdf_images(
        doc_id: str,    
        valid_request: bool = Depends(validate_session_doc_pair),
    ):

    url_list = []

    if not valid_request:
        raise HTTPException(
            status_code=403,
            detail="User not authorized to access this document or invalid document ID",
        )
    job = load_job(doc_id=doc_id, job_type="extraction")
    if not job:
        raise HTTPException(
            status_code=404, 
            detail="Document ID not found"
        )
    
    if job.get("status") == "processing":
        raise HTTPException(
            status_code=202,
            detail="The document is still being processed. Please try again later."
        )

    prefix = f"{doc_id}/images/"
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
    keys = [obj['Key'] for page in pages for obj in page.get('Contents', [])]
    
    for key in keys:
        url = generate_presigned_url(key)
        url_list.append(ImageData(image_key=key, url=url))

    return ImageResponse(doc_id=doc_id, filename=f"{doc_id}.pdf", images=url_list)