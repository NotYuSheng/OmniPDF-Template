from pydantic import BaseModel


class TextChunkData(BaseModel):
    chunk_id: int
    page: int
    chunk: str


class TextChunksResponse(BaseModel):
    doc_id: str
    filename: str
    chunks: list[TextChunkData]
