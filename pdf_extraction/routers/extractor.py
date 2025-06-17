from fastapi import APIRouter, File, UploadFile, HTTPException
import uuid
import logging
from shared_utils.s3_utils import upload_fileobj, generate_presigned_url, delete_file, s3_client, S3_BUCKET
from models.document import DocumentUploadResponse

from docling.document_converter import DocumentConverter
import json
import time
import requests

start_time = time.time()

router = APIRouter()
logger = logging.getLogger(__name__)



@router.post("/extract", response_model=DocumentUploadResponse)
def pdf_extraction(doc_id: str):
    # r = requests.get(f"http://localhost:8000/documents/{doc_id}")
    r = requests.get(f"http://pdf_processor_service:8000/documents/{doc_id}")

    r.raise_for_status()

    converter = DocumentConverter()
    result = converter.convert(r.json()['download_url'])
    data = result.document.export_to_dict()

    for ref in ['body', 'groups']:
        if ref in data.keys():
            data.pop(ref)

    with open('./result.json', 'w') as fp:
        json.dump(data, fp, indent=4)

    elapsed_time = time.time() - start_time
    logger.info(f"Extraction Completed in {elapsed_time:.2f} seconds")

    return data  # If you want to return something
