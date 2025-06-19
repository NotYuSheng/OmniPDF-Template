from pydantic import BaseModel


class ImageData(BaseModel):
    image_id: int
    page: int
    base64: bytes


class ImageResponse(BaseModel):
    doc_id: str
    filename: str
    tables: list[ImageData]
