from fastapi import APIRouter, HTTPException
import logging
from models.extractor import PDFDataResponse

from docling.document_converter import DocumentConverter
import json
import time
import requests
import torch

start_time = time.time()

router = APIRouter(prefix="/extractor", tags=["extractor"])
logger = logging.getLogger(__name__)



@router.post("/extract", response_model=PDFDataResponse)
def pdf_extraction(doc_id: str):
    # r = requests.get(f"http://localhost:8000/documents/{doc_id}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    try:
        r = requests.get(f"http://pdf_processor_service:8000/documents/{doc_id}")
        # r.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found.")
        else:
            logger.error(f"HTTP error occurred: {http_err}")
            raise HTTPException(status_code=r.status_code, detail="Error fetching document.")
    except requests.exceptions.RequestException as err:
        logger.error(f"Request error occurred: {err}")
        raise HTTPException(status_code=500, detail="Failed to connect to the document service.")

    try:
        converter = DocumentConverter()
        result = converter.convert(r.json()['download_url'])
        data = result.document.export_to_dict()

        for ref in ['body', 'groups']:
            data.pop(ref, None)

        with open('./result.json', 'w') as fp:
            json.dump(data, fp, indent=4)

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

    except Exception as e:
        logger.exception("Docling failed to convert the document.")
        raise HTTPException(status_code=500, detail=f"Failed to process the document with Docling.\n{e}")

