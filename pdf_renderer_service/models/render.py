from pydantic import BaseModel, HttpUrl
from typing import Optional

class DocumentRendererResponse(BaseModel):
    doc_id: str
    filename: str
    download_url: Optional[HttpUrl]