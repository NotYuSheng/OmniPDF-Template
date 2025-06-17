from fastapi import FastAPI
from routers import health
from routers import document
from routers.sessions import sessions
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

app.include_router(health.router)
app.include_router(document.router)
app.include_router(sessions.router)
