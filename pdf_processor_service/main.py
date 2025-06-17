from fastapi import FastAPI
from routers import health
from routers.documents import upload, tables, images, text_chunks
from routers.sessions import sessions
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

app.include_router(health.router)
app.include_router(upload.router, prefix="/documents")
app.include_router(tables.router, prefix="/documents")
app.include_router(images.router, prefix="/documents")
app.include_router(text_chunks.router, prefix="/documents")
app.include_router(sessions.router)
# app.include_router(tables.router, prefix="/documents")
# app.include_router(images.router, prefix="/documents")
# app.include_router(text_chunks.router, prefix="/documents")
