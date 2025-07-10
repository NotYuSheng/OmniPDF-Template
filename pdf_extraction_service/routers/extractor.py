from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging
import time
import io

from models.extractor import ExtractResponse
from shared_utils.s3_utils import (
    save_job, 
    load_job,
    upload_fileobj,
)

from docling_core.types.doc import PictureItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from shared_utils.redis import RedisSimpleFileFlag

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)
redis_flag = RedisSimpleFileFlag()

def process_pdf(doc_id: str, presign_url: str, img_scale: float = 2.0):
    start_time = time.time()

    opts = PdfPipelineOptions()
    opts.images_scale = img_scale
    opts.generate_picture_images = True
    opts.generate_table_images = False
    opts.generate_page_images = True

    opts.accelerator_options = AcceleratorOptions(
        num_threads=4, device=AcceleratorDevice.AUTO
    )
    
    try:
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )
        result = converter.convert(presign_url)
        data = result.document.export_to_dict()

        for ref in ['body', 'groups']:
            data.pop(ref, None)

        pic_cnt = -1
        for element, _ in result.document.iterate_items():
            if isinstance(element, PictureItem):
                pic_cnt += 1
                key = f"{doc_id}/images/img_{pic_cnt}.png"
                img = element.get_image(result.document)
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                success = upload_fileobj(buffer, key, content_type="image/png")
                redis_flag.set(key)
                if not success:
                    logger.warning(detail=f"Failed to upload picture {pic_cnt} to S3")

                data["pictures"][pic_cnt]["key"] = f"img_{pic_cnt}.png"
                data["pictures"][pic_cnt].get("image", {}).pop("uri", None)
                
            else:
                continue
            
            pages = data.get("pages", {})
            for page in pages.values():
                image = page.get("image", {})
                if isinstance(image, dict):
                    image.pop("uri", None)
        

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
async def submit_pdf(doc_id: str, download_url: str, background_tasks: BackgroundTasks):
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