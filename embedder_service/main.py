from fastapi import FastAPI
from routers import health, embed
import logging


# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(root_path="/embedder")

app.include_router(health.router)
app.include_router(embed.router)
