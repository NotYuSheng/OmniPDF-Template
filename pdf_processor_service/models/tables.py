from pydantic import BaseModel


class TableData(BaseModel):
    table_id: int
    page: int
    csv: str


class TablesResponse(BaseModel):
    doc_id: str
    filename: str
    tables: list[TableData]
