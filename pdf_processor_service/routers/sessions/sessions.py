from fastapi import Depends, APIRouter, Response

from utils.redis import (
    deleteSession,
    getDocList,
    getSessionId,
    getSessionStorage,
    setDocList,
    SessionStorage,
    createNewSession,
    validateSessionId,
)
from models.session import SessionResponse, SessionDataResponse

router = APIRouter()


@router.post("/Session")
async def _setSession(
    filelist: list[str],
    response: Response,
    sessionStorage: SessionStorage = Depends(getSessionStorage),
    sessionId: str = Depends(getSessionId),
    sessionData: list[str] = Depends(getDocList),
    validSession: bool = Depends(validateSessionId)
):
    if filelist:
        sessionData = filelist
        if validSession:
            setDocList(sessionId, sessionData, sessionStorage)
        else:
            sessionId = createNewSession(response, sessionStorage=sessionStorage)
    return SessionDataResponse(session_id=sessionId, session_data=sessionData)


@router.get("/Session")
async def _getSessionId(
    sessionId: str = Depends(getSessionId),
    validSession: bool = Depends(validateSessionId)
):
    return SessionResponse(session_id=sessionId, valid_session=validSession)


@router.delete("/Session")
async def _deleteSession(
    response: Response,
    sessionId: str = Depends(getSessionId),
    sessionStorage: SessionStorage = Depends(getSessionStorage)
):
    deleteSession(response, sessionId, sessionStorage)
    return "ok"
