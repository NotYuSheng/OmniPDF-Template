from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import logging
import time

from models.extractor import ExtractResponse
from docling.document_converter import DocumentConverter
from shared_utils.s3_utils import save_job, load_job

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

        job_data = {
            "doc_id": doc_id,
            "status": "complete",
            "result": {
                "schema_name": data.get('schema_name', ""),
                "version": data.get('version', ""),
                "name": data.get('name', ""),
                "origin": data.get('origin', {}),
                "furniture": data.get('furniture', {}),
                "texts": data.get('texts', []),
                "pictures": data.get('pictures', []),
                "tables": data.get('tables', []),
                "key_value_items": data.get('key_value_items', []),
                "form_items": data.get('form_items', []),
                "pages": data.get('pages', {})
            }
        }

        save_job(doc_id, job_data)
        logger.info(f"Time to process PDF: {time.time() - start_time}")

    except Exception as e:
        logger.exception(f"Docling failed to convert the document for doc_id: {doc_id} - {e}")
        error_job = {
            "doc_id": doc_id,
            "status": "error",
            "message": "Failed to download or parse document"
        }
        save_job(doc_id, error_job)

@router.post("/extract", response_model=ExtractResponse, status_code=202)
def submit_pdf(doc_id: str, download_url: str, background_tasks: BackgroundTasks):
    save_job(doc_id, {
        "doc_id": doc_id,
        "status": "processing"
    })

    background_tasks.add_task(process_pdf, doc_id, download_url)
    return ExtractResponse(doc_id=doc_id, status="processing")

@router.get("/{doc_id}", response_model=ExtractResponse)
def get_status(doc_id: str):
    job = load_job(doc_id)
    if not job:
        raise HTTPException(status_code=404, detail="Document ID not found")

    if job.get("status") == "error":
        raise HTTPException(status_code=500, detail=job.get("message", "Processing failed"))

    if job.get("status") == "processing":
        return JSONResponse(status_code=204, content=job)

    return ExtractResponse(**job)
