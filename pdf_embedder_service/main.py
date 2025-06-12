from fastapi import FastAPI
from routers import health, embed, embed_status
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


app = FastAPI(swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}})

app.include_router(health.router)
app.include_router(embed.router)
app.include_router(embed_status.router)


# For self-testing purposes only
@app.get("/")
def my_first_get_api():
    return {"message": "First FastAPI example"}


@app.get("/users/{username}")
def read_user(username: str):
    return {"message": f"Hello {username}"}
