from fastapi import FastAPI
from routers import health
from docling_translation_service.routers import translation
from routers import session
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

app.include_router(health.router)
app.include_router(translation.router)
app.include_router(session.router)
