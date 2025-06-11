from fastapi import FastAPI
from routers import health
from routers.documents import upload
#from routers.documents import upload, tables, images, text_chunks

app = FastAPI()

app.include_router(health.router)
app.include_router(upload.router, prefix="/documents")
#app.include_router(tables.router, prefix="/documents")
#app.include_router(images.router, prefix="/documents")
#app.include_router(text_chunks.router, prefix="/documents")