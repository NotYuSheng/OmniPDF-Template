import pymupdf
import logging
import io
import uuid
import requests
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from models.render import DocumentRendererResponse

from shared_utils.s3_utils import (
    upload_fileobj,
    generate_presigned_url,
)

router = APIRouter(prefix="/render", tags=["render"])
logger = logging.getLogger(__name__)

@router.post("/{doc_id}")
async def pdf_render(doc_url: str,
               json_url: str):

    response = requests.get(json_url)
    response.raise_for_status()
    json_data = response.json()

    transtext_data = defaultdict(list)

    texts = json_data.get("docling", {}).get("texts", [])
    for text_item in texts:
        translated = text_item.get("translated_text", "")
        for prov in text_item.get("prov", []):
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")
            if page_no is not None and bbox:
                transtext_data[page_no].append({
                    "translated_text": translated,
                    "bbox": bbox
                })
    data = dict(transtext_data)



    ### Table handler ###
    trans_table_data = defaultdict(list)

    tables = json_data.get("docling", {}).get("tables", [])
    for table in tables:
        translated = text_item.get("translated_text", "")
        for prov in text_item.get("prov", []):
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")
            if page_no is not None and bbox:
                transtext_data[page_no].append({
                    "translated_text": translated,
                    "bbox": bbox
                })
    data = dict(transtext_data)



    pdf_response = requests.get(doc_url)
    pdf_response.raise_for_status()
    doc = pymupdf.open(stream=pdf_response.content, filetype="pdf")

    for page in doc:
        logger.info(f"{page.number}\n") 
        blocks = page.get_text("blocks") 
        for block in blocks:
            rect = block[:4] 

            page.add_redact_annot(rect)

        page.apply_redactions()
        page.clean_contents()

        data_lst = data[page.number + 1]
        for trans_data in data_lst:
            trans_text = trans_data["translated_text"]
            bbox = trans_data['bbox']
            coords = (bbox["l"], (page.rect[3]- bbox["t"]), bbox["r"], page.rect[3]- bbox["b"])
            page.insert_htmlbox(coords, trans_text)
            
            logger.info(f"Text: {trans_text}")
            logger.info(f"Bbox: {coords}")
            
    buffer = io.BytesIO()
    doc.save(buffer, garbage=3, deflate=True)
    buffer.seek(0)  # Reset buffer position

    doc_id = str(uuid.uuid4())
    key = f"{doc_id}/rendered.pdf"

    try:
        success = upload_fileobj(
            buffer, key, content_type="application/pdf"
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")

        presigned_url = generate_presigned_url(key)

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    return(DocumentRendererResponse(doc_id=doc_id,
                                    filename=key,
                                    download_url=presigned_url,
                                    )
                                )
