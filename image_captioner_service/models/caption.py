from pydantic import BaseModel

class ImageCaptioningResponse(BaseModel):
    doc_id: str
    image_id: str 
    caption: str 
