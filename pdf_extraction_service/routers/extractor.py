from fastapi import APIRouter, HTTPException
import logging
from models.extractor import PDFDataResponse

from docling.document_converter import DocumentConverter
import json
import time
import requests
import torch

router = APIRouter(prefix="/extractor", tags=["extractor"])
logger = logging.getLogger(__name__)



@router.post("/extract", response_model=PDFDataResponse)
def pdf_extraction(doc_id: str):
    start_time = time.time()

    # r = requests.get(f"http://localhost:8000/documents/{doc_id}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    try:
        r = requests.get(f"http://pdf_processor_service:8000/documents/{doc_id}")
        r.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.HTTPError as http_err:
        # http_err.response contains the response object
        if http_err.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found.")
        else:
            logger.error(f"HTTP error occurred while fetching document: {http_err} - {http_err.response.text}")
            raise HTTPException(status_code=http_err.response.status_code, detail="Error fetching document.")
    except requests.exceptions.RequestException as err:
        logger.error(f"Request error occurred while fetching document: {err}")
        raise HTTPException(status_code=500, detail="Failed to connect to the document service.")
    try:
        converter = DocumentConverter()
        result = converter.convert(r.json()['download_url'])
        data = result.document.export_to_dict()

        for ref in ['body', 'groups']:
            data.pop(ref, None)

        elapsed_time = time.time() - start_time

        # Docling had an issue of an excessively long processing time
        # This no longer occurs but take note if it occurs again (e.g. 5 min for a small pdf document where is should be a few seconds)
        logger.info(f"Extraction Completed in {elapsed_time:.2f} seconds")

        return PDFDataResponse(
            schema_name = data['schema_name'],
            version = data['version'],
            name =  data['name'],
            origin = data['origin'],
            furniture = data['furniture'],
            texts = data['texts'],
            pictures = data['pictures'],
            tables = data['tables'],
            key_value_items = data['key_value_items'],
            form_items = data['form_items'],
            pages = data['pages']
        )

    except Exception:
        logger.exception("Docling failed to convert the document.")
        raise HTTPException(status_code=500, detail="Failed to process the document with Docling. Please check server logs for more details.")
