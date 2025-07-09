import requests
import pymupdf
import json
import time
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
import logging
import httpx
from collections import defaultdict

from shared_utils.s3_utils import (
    upload_fileobj,
    generate_presigned_url,
    delete_file,
    s3_client,
    S3_BUCKET,
)

router = APIRouter(prefix="/render", tags=["render"])
logger = logging.getLogger(__name__)

@router.post("/{doc_id}")
async def pdf_render(doc_url: str,
               json_url: str):

    start_time = time.time()

    async with httpx.AsyncClient() as client:
        response = await client.get(json_url)
        
    if response.status_code == 200:
        data = response.json()  # Convert JSON response to Python dict

    pagewise_data = defaultdict(list)

    texts = data.get("docling", {}).get("texts", [])
    for text_item in texts:
        translated = text_item.get("translated_text", "")
        for prov in text_item.get("prov", []):
            page_no = prov.get("page_no")
            bbox = prov.get("bbox")
            if page_no is not None and bbox:
                pagewise_data[page_no].append({
                    "translated_text": translated,
                    "bbox": bbox
                })


    doc = pymupdf.open(doc_url)
    for page in doc:
        print(f"{page.number}\n") 
        blocks = page.get_text("blocks")  # list of tuples: (x0, y0, x1, y1, "text", block_no, block_type)
        for block in blocks:
            rect = block[:4]  # (x0, y0, x1, y1)

            page.add_redact_annot(rect)

        page.apply_redactions()
        page.clean_contents()
        try:
            page_lst = data[page.number + 1]
            for i in page_lst:
                new_text = i["text"]
                bbox = i["prov"][0]['bbox']
                coords = (bbox["l"], (page.rect[3]- bbox["t"]), bbox["r"], page.rect[3]- bbox["b"])
                translation = translate(new_text)
                print(f"Text: {new_text}")
                print(f"Translation: {translation}")
                print(f"Bbox: {coords}")

                page.draw_rect(coords, color=(1, 0, 1))
                status = page.insert_htmlbox(coords, translation) # fontsize=font_size, fontname=font_name, color=text_color, align=0
                print(f"Status: {status}")
        except KeyError:
            pass
    doc.save("./output_white_boxed.pdf", garbage=3, deflate=True)

    print(f"Translation complete in {time.time() - start_time}")