from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """
    Request model for chat API endpoints.
    """

    message: str
    id: Optional[str] = None
