from fastapi import FastAPI
from routers import health, document
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

app.include_router(health.router)
app.include_router(document.router)
