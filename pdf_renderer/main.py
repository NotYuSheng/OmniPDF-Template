from fastapi import FastAPI
from routers import health
from pdf_extraction.routers.pdf_extraction import extractor
#from routers.documents import upload, tables, images, text_chunks
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

app.include_router(health.router)
app.include_router(extractor.router, prefix="/render")