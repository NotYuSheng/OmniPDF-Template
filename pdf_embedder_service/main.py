from fastapi import FastAPI
from routers import health, embed, embed_status
import logging


# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}})

# /Health endpoint
app.include_router(health.router)
# /Embed endpoint
app.include_router(embed.router)
# /Status/{doc_id} endpoint
app.include_router(embed_status.router)
