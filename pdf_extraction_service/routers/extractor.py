from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging
from models.extractor import ExtractResponse, PDFDataResponse
from docling.document_converter import DocumentConverter
from storage.job_store import job_store
import time

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

def process_pdf(doc_id: str, presign_url: str):
    start_time = time.time()
    try:
        converter = DocumentConverter()
        result = converter.convert(presign_url)
        data = result.document.export_to_dict()

        for ref in ['body', 'groups']:
            data.pop(ref, None)

        job_store[doc_id] = {
            "doc_id": doc_id,
            "status": "complete",
            "result": PDFDataResponse(
                schema_name = data.get('schema_name', ""),
                version = data.get('version', ""),
                name = data.get('name', ""),
                origin = data.get('origin', {}),
                furniture = data.get('furniture', {}),
                texts = data.get('texts', []),
                pictures = data.get('pictures', []),
                tables = data.get('tables', []),
                key_value_items = data.get('key_value_items', []),
                form_items = data.get('form_items', []),
                pages = data.get('pages', {})
            )
        }

        logger.info(f"Time to process PDF: {time.time() - start_time}")

    except Exception:
        logger.exception("Docling failed to convert the document.")
        job_store[doc_id] = {
            "doc_id": doc_id,
            "status": "error",
            "message": "Failed to download or parse document"
        }

@router.post("/extract", response_model=ExtractResponse)
def submit_pdf(doc_id: str, download_url: str, background_tasks: BackgroundTasks):

    job_store[doc_id] = {
        "doc_id": doc_id,
        "status": "processing"
    }
    
    background_tasks.add_task(process_pdf, doc_id, download_url)
    return ExtractResponse(doc_id=doc_id, status="processing")


@router.get("/{doc_id}", response_model=ExtractResponse)
def get_status(doc_id: str):
    job = job_store.get(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail="Document ID not found")

    return ExtractResponse(**job)
