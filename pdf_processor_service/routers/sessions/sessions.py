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
async def _set_session(
    filelist: list[str],
    response: Response,
    sessionStorage: SessionStorage = Depends(get_session_storage),
    sessionId: str = Depends(get_session_id),
    sessionData: list[str] = Depends(get_doc_list),
    validSession: bool = Depends(validate_session_id)
):
    if filelist:
        sessionData = filelist
        if validSession:
            set_doc_list(sessionId, sessionData, sessionStorage)
        else:
            sessionId = create_new_session(response, sessionStorage=sessionStorage)
    return SessionDataResponse(session_id=sessionId, session_data=sessionData)


@router.get("/session")
async def _get_session_id(
    sessionId: str = Depends(get_session_id),
    validSession: bool = Depends(validate_session_id)
):
    return SessionResponse(session_id=sessionId, valid_session=validSession)


@router.delete("/session")
async def _delete_session(
    response: Response,
    sessionId: str = Depends(get_session_id),
    sessionStorage: SessionStorage = Depends(get_session_storage)
):
    delete_session(response, sessionId, sessionStorage)
    return "ok"
