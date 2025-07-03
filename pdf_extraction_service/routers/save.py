from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging
import time
import io

from models.extractor import ExtractResponse
from shared_utils.s3_utils import save_job, load_job, upload_fileobj
from pathlib import Path

from docling_core.types.doc import PictureItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

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

        save_job(doc_id = doc_id, 
                 job_data = job_data, 
                 status = "completed", 
                 job_type = "extraction"
                 )
        
        logger.info(f"Time to process PDF: {time.time() - start_time}")

    except Exception as e:
        logger.exception(f"Docling failed to convert the document for doc_id: {doc_id} - {e}")
        error_job = {
            "doc_id": doc_id,
            "status": "error",
            "message": "Failed to download or parse document"
        }
        save_job(doc_id = doc_id, 
                 job_data = error_job, 
                 status = "failed", 
                 job_type = "extraction"
                 )

@router.post("/extract", response_model=ExtractResponse, status_code=202)
def submit_pdf(doc_id: str, download_url: str, background_tasks: BackgroundTasks):
    save_job(doc_id = doc_id, 
             job_data = {}, 
             status = "processing", 
             job_type = "extraction"
             )

    background_tasks.add_task(process_pdf, doc_id, download_url)
    return ExtractResponse(doc_id=doc_id, status="processing")

@router.get("/{doc_id}", response_model=ExtractResponse)
async def get_status(doc_id: str):
    job = load_job(doc_id=doc_id, job_type="extraction")
    if not job:
        raise HTTPException(status_code=404, detail="Document ID not found")

    if job.get("status") == "failed":
        error_message = job.get("data", {}).get("message", "Processing failed")
        raise HTTPException(status_code=500, detail=error_message)
    
    job_data = job.get("data", {})
    result = job_data.get("result", None)

    return ExtractResponse(
        doc_id=doc_id,
        status=job.get("status", "unknown"),
        result=result
    )