from fastapi import APIRouter
import logging
import httpx
from collections import defaultdict
from typing import Literal
import json

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
    json_path: str,
    json_name: Literal["original", "translated"]
    ):

    if not json_path:
        return {"error": "At least one of pdf_path or json_path must be provided."}

    if json_path:
        try:
            key = f"{doc_id}/{json_name}.json"
            with open(json_path, "rb") as f:
                upload_fileobj(f, key, "application/json")
            print(f"✅ Uploaded {json_path} to s3")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
