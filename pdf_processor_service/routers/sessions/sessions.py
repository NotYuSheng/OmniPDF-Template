from fastapi import Depends, APIRouter, Request, Response

from utils.redis import deleteSession, getDocList, getSessionId, getSessionStorage, setDocList, SessionStorage, createSession

router = APIRouter()


@router.post("/Session")
async def _setSession(
    filelist: list[str], response: Response, sessionStorage: SessionStorage = Depends(getSessionStorage), sessionId: str = Depends(getSessionId), sessionData: list[str] = Depends(getDocList)
):
    if filelist:
        sessionData = filelist
        if sessionId:
            setDocList(sessionId, sessionData, sessionStorage)
        else:
            sessionId = createSession(response, sessionData, sessionStorage)
    return {
        "sessionId": sessionId,
        "sessionData": sessionData
    }


@router.get("/Session")
async def _getSessionId(sessionId: str = Depends(getSessionId)):
    return sessionId


@router.delete("/Session")
async def _deleteSession(
    response: Response, sessionId: str = Depends(getSessionId), sessionStorage: SessionStorage = Depends(getSessionStorage)
):
    deleteSession(response, sessionId, sessionStorage)
    return None
