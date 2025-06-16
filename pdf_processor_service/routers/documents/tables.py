from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import logging
from s3_utils import get_file
from utils.redis import validate_session_doc_pair
from tempfile import TemporaryFile

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{doc_id}/tables")
async def _get_pdf_tables_from_s3(doc_id: str, valid_session: bool = Depends(validate_session_doc_pair)):
    if not valid_session:
        raise HTTPException(status_code=403, detail="Failed to upload file to S3")
    
    with TemporaryFile() as f:
        get_file(f"{doc_id}_tables.csv", f)
        f.seek(0)
        return StreamingResponse(content=f, media_type="text/csv")
