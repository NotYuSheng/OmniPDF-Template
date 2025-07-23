import pymupdf
import logging
import io
import uuid
import time
import requests
from PyPDF2 import PdfReader, PdfWriter
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from models.render import DocumentRendererResponse
from spire.pdf import PdfCompressor

import tempfile
import os
from io import BytesIO


from shared_utils.s3_utils import (
    upload_fileobj,
    generate_presigned_url,
)

router = APIRouter(prefix="/render", tags=["render"])
logger = logging.getLogger(__name__)

def compress_in_chunks_spire(input_bytes: bytes, chunk_size: int = 10) -> bytes:
    # 1) Load pages via PyPDF2
    reader = PdfReader(BytesIO(input_bytes))
    total_pages = len(reader.pages)
    compressed_segments = []

    # 2) Process each 10-page slice
    for start in range(0, total_pages, chunk_size):
        # build a slice
        writer = PdfWriter()
        for page in reader.pages[start : start + chunk_size]:
            writer.add_page(page)
        slice_buf = BytesIO()
        writer.write(slice_buf)
        slice_buf.seek(0)

        # write slice to disk for Spire.PDF compressor
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(slice_buf.getvalue())
            tmp.flush()
            tmp_path = tmp.name

        # compress with Spire.PDF
        compressor = PdfCompressor(tmp_path)
        opts = compressor.OptimizationOptions
        opts.SetIsCompressFonts(True)
        compressor.CompressToFile(tmp_path)

        # read back compressed bytes
        with open(tmp_path, "rb") as f:
            compressed_segments.append(f.read())

        os.remove(tmp_path)

    # 3) Merge all compressed slices
    final_writer = PdfWriter()
    for segment in compressed_segments:
        seg_reader = PdfReader(BytesIO(segment))
        for p in seg_reader.pages:
            final_writer.add_page(p)

    out_buf = BytesIO()
    final_writer.write(out_buf)
    return out_buf.getvalue()

@router.post("/{doc_id}")
async def pdf_render(doc_url: str,
               json_url: str):

    start_time = time.time()

    response = requests.get(json_url)
    response.raise_for_status()
    json_data = response.json()

    pdf_response = requests.get(doc_url)
    pdf_response.raise_for_status()
    doc = pymupdf.open(stream=pdf_response.content, filetype="pdf")

    trans_text_data = defaultdict(list)

    texts = json_data.get("docling", {}).get("texts", [])

    for text_item in texts:
        translated = text_item.get("translated_text", "")

        for prov in text_item.get("prov", []):
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")

            bbox["b"] = doc[page_no-1].rect[3] - bbox["b"]
            bbox["t"] = doc[page_no-1].rect[3] - bbox["t"]

            if page_no is not None and bbox:
                trans_text_data[page_no].append({
                    "translated_text": translated,
                    "bbox": bbox
                })

    ### This section is supposed to handle table rendering but has been excluded due to autoscaling issues
    tables = json_data.get("docling", {}).get("tables", [])

    for table in tables:
        table_cells = table.get("data", {}).get("table_cells", [])
        page_no = table.get("prov", [])[0].get("page_no")

        for cell in table_cells:
            translated = cell.get("translated_text")
            bbox = cell.get("bbox")

            if page_no is not None and bbox:
                trans_text_data[page_no].append({
                    "translated_text": translated,
                    "bbox": bbox
                })

    data = dict(trans_text_data)

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

            coords = (bbox["l"], bbox["t"], bbox["r"], bbox["b"])

            logger.info(f"Text: {trans_text}")
            logger.info(f"Bbox: {coords}")
            try:
                page.insert_htmlbox(coords, trans_text)
            except Exception as e:
                logger.error("Error inserting HTML box:")
                logger.error(f"Text: {trans_text}")
                logger.error(f"Original BBox: {bbox}")
                logger.error(f"Converted Coords: {coords}")
                logger.error(f"Page size: {page.rect}")
                logger.exception(e)  # full traceback
                raise e  # optionally re-raise for FastAPI to return 500

    original_buffer = io.BytesIO()
    doc.subset_fonts()
    doc.save(original_buffer, garbage=4, deflate=True, clean=True)
    original_buffer.seek(0)  # Reset buffer position

    compressed_buffer = io.BytesIO()

    reader = PdfReader(original_buffer)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # Write to a new BytesIO buffer
    compressed_buffer = io.BytesIO()
    writer.write(compressed_buffer)
    compressed_buffer.seek(0)



    compressed_buffer = compressed_buffer.getvalue()
    compressed_bytes = compress_in_chunks_spire(compressed_buffer, chunk_size=10)
    compressed_buffer = io.BytesIO(compressed_bytes)



    file_size = len(compressed_buffer.getvalue())

    logger.info(f"Time to render document: {time.time() - start_time}")
    logger.info(f"File size: {file_size / 1024:.2f} KB")
    logger.info(f"File size: {file_size / (1024 * 1024):.2f} MB")

    doc_id = str(uuid.uuid4())
    key = f"{doc_id}/rendered.pdf"

    try:
        success = upload_fileobj(
            compressed_buffer, key, content_type="application/pdf"
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
