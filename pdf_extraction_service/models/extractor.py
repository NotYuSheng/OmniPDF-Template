from pydantic import BaseModel, HttpUrl
from typing import Optional

class PDFDataResponse(BaseModel):
    schema_name: str
    version: str 
    name: str 
    origin: dict 
    furniture: dict
    texts: list
    pictures: list
    tables: list
    key_value_items: list
    form_items: list
    pages: dict