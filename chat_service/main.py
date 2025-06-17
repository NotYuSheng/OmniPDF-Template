from fastapi import FastAPI
from routers import health, message
from routers.chat import handler

import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

app.include_router(health.router)
app.include_router(message.router)
app.include_router(handler.router, prefix="/chat")
