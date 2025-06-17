from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    id: Optional[str] = None
