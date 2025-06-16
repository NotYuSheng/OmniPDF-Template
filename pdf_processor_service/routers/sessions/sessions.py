from fastapi import Depends, APIRouter, Response

from utils.redis import (
    delete_session,
    get_doc_list,
    get_session_id,
    get_session_storage,
    set_doc_list,
    SessionStorage,
    create_new_session,
    validate_session_id,
)
from models.session import SessionResponse, SessionDataResponse

router = APIRouter()


@router.post("/session")
async def set_session(
    file_list: list[str],
    response: Response,
    session_storage: SessionStorage = Depends(get_session_storage),
    session_id: str = Depends(get_session_id),
    session_data: list[str] = Depends(get_doc_list),
    valid_session: bool = Depends(validate_session_id)
):
    if file_list:
        session_data = file_list
        if valid_session:
            set_doc_list(session_id, session_data, session_storage)
        else:
            session_id = create_new_session(response, session_storage=session_storage)
    return SessionDataResponse(session_id=session_id, session_data=session_data)


@router.get("/session")
async def get_session_id(
    session_id: str = Depends(get_session_id),
    valid_session: bool = Depends(validate_session_id)
):
    return SessionResponse(session_id=session_id, valid_session=valid_session)


@router.delete("/session")
async def delete_session(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage)
):
    delete_session(response, session_id, session_storage)
    return "ok"
