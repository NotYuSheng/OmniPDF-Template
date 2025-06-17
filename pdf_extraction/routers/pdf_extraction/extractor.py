from docling.document_converter import DocumentConverter
import json
import time
from fastapi import APIRouter, UploadFile, File
import logging

start_time = time.time()

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/extract")
def pdf_extraction(file: UploadFile = File(...)):
    # source = r"/home/ubuntu/Desktop/OmniPDF/sample-files/o_level_paper_2.pdf"  # document per local path or URL
    converter = DocumentConverter()
    result = converter.convert(file)
    data = result.document.export_to_dict()

    for ref in ['body', 'groups']:
        if ref in data.keys():
            data.pop(ref)
    with open('./result.json', 'w') as fp:
        json.dump(data, fp, indent=4)

    print(f"Extraction Completed in {time.time() - start_time}")

    return data