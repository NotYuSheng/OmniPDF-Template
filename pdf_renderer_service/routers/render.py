import pymupdf
import time
from fastapi import APIRouter, HTTPException
import logging
import httpx
import requests
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

    # async with httpx.AsyncClient() as client:
    #     response = await client.get(json_url)

    # if response.status_code != 200:
    #     logger.error(f"❌ Failed to fetch JSON: {response.status_code} - {response.text}")
    #     raise HTTPException(status_code=500, detail="Failed to fetch JSON file from URL")

    # json_data = response.json()  # Convert JSON response to Python dict



    # with open(json_url, "r", encoding="utf-8") as f:
    #     json_data = json.load(f)



    response = requests.get(json_url)
    response.raise_for_status()
    json_data = response.json()


    pagewise_data = defaultdict(list)

    texts = json_data.get("docling", {}).get("texts", [])
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
    data = dict(pagewise_data)

    pdf_response = requests.get(doc_url)
    pdf_response.raise_for_status()  # will raise if the PDF couldn't be fetched
    doc = pymupdf.open(stream=pdf_response.content, filetype="pdf")

    for page in doc:
        print(f"{page.number}\n") 
        blocks = page.get_text("blocks")  # list of tuples: (x0, y0, x1, y1, "text", block_no, block_type)
        for block in blocks:
            rect = block[:4]  # (x0, y0, x1, y1)

            page.add_redact_annot(rect)

        page.apply_redactions()
        page.clean_contents()

        data_lst = data[page.number + 1]
        for trans_data in data_lst:
            trans_text = trans_data["translated_text"]
            bbox = trans_data['bbox']
            coords = (bbox["l"], (page.rect[3]- bbox["t"]), bbox["r"], page.rect[3]- bbox["b"])
            print(f"Text: {trans_text}")
            print(f"Bbox: {coords}")

            page.draw_rect(coords, color=(1, 0, 1))
            status = page.insert_htmlbox(coords, trans_text) # fontsize=font_size, fontname=font_name, color=text_color, align=0
            print(f"Status: {status}")

    doc.save("./output.pdf", garbage=3, deflate=True)

    print(f"Translation complete in {time.time() - start_time}")