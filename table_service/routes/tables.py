from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from services.table_extractor import extract_tables_from_pdf, get_cached_xlsx_path
import os

router = APIRouter(prefix="/tables", tags=["Tables"])

# Path constants
PDF_DIR = "/data/pdfs"
EXPORT_DIR = "/data/exports"

# Dummy session check placeholder
def verify_session(doc_id: str):
    # TODO: Replace with actual Redis logic
    return True

@router.post("/{doc_id}")
async def extract_tables(doc_id: str, _=Depends(verify_session)):
    pdf_path = os.path.join(PDF_DIR, f"{doc_id}.pdf")
    export_path = os.path.join(EXPORT_DIR, f"{doc_id}.xlsx")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found.")

    try:
        extract_tables_from_pdf(pdf_path, export_path)
        return FileResponse(export_path, filename=f"{doc_id}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}")
async def get_tables(doc_id: str, _=Depends(verify_session)):
    export_path = get_cached_xlsx_path(doc_id)
    if not os.path.exists(export_path):
        raise HTTPException(status_code=404, detail="Extracted table not found.")
    return FileResponse(export_path, filename=f"{doc_id}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.delete("/{doc_id}")
async def delete_tables(doc_id: str, _=Depends(verify_session)):
    export_path = get_cached_xlsx_path(doc_id)
    if os.path.exists(export_path):
        os.remove(export_path)
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="No extracted table to delete.")
