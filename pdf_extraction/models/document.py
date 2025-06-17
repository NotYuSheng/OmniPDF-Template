from pydantic import BaseModel, HttpUrl
from typing import Optional

class DocumentUploadResponse(BaseModel):
    schema_name: str
    version: str
    name: str
    origin: dict