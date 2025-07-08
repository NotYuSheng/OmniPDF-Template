from fastapi import FastAPI
from routers import health, cleaner
import logging

from utils.cleaner import setup_redis_watcher

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

setup_redis_watcher()

app = FastAPI(root_path="/cleaner")

app.include_router(health.router)
app.include_router(cleaner.router)
