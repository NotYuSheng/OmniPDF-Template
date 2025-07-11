from fastapi import APIRouter, File, UploadFile
import logging
import httpx
from collections import defaultdict
from typing import Literal
from models.bypass import BypassResponse
import io

from shared_utils.s3_utils import (
    upload_fileobj,
    generate_presigned_url,
    delete_file,
    s3_client,
    S3_BUCKET,
)


router = APIRouter(prefix="/bypass", tags=["bypass"])
logger = logging.getLogger(__name__)

@router.post("/{doc_id}")
async def dump_files(
    doc_id: str,
    json_name: Literal["original", "translated"],
    json_file: UploadFile = File(...),
    ):

    try:
        key = f"{doc_id}/{json_name}.json"

        # Read the uploaded file as bytes
        file_content = await json_file.read()
        file_like = io.BytesIO(file_content)  # Wrap in file-like object

        # Upload to S3
        upload_fileobj(file_like, key, "application/json")

        logger.info(f"✅ Uploaded {key} to S3")

        return BypassResponse(
            doc_id=doc_id,
            filename=key,
            download_url=generate_presigned_url(key),
        )

    except Exception as e:
        logger.warning(f"❌ Upload failed: {e}")
        return {"error": "Error"}
