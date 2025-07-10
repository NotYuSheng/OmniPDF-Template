from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI

from routers import health, cleaner
from utils.cleaner import setup_redis_watcher_thread

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # load the redis watcher
    _, watcher, watcher_thread = await setup_redis_watcher_thread()
    logger.info(f"{watcher_thread}")
    yield
    # stop the watcher
    watcher_thread.stop()
    logger.info("Stopped well")


app = FastAPI(root_path="/cleaner", lifespan=lifespan)
# app = FastAPI(root_path="/cleaner")

app.include_router(health.router)
app.include_router(cleaner.router)
