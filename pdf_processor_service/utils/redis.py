# Original code from https://github.com/duyixian1234/fastapi-redis-session
# Updated for package versions listed in requirements.txt

from os import getenv
from datetime import timedelta
from typing import Callable, Optional
from uuid import uuid4

from pydantic_settings import BaseSettings

from typing import Any, Generator

from fastapi import Depends, Request, Response
import pickle
from typing import Any, Callable

from redis import Redis

# Stores the data as string using python pickle


class SessionStorage:
    def __init__(self):
        self.client = Redis.from_url(config.redisURL)

    def __getitem__(self, key: str):
        raw = self.client.get(key)
        return raw and pickle.loads(raw)

    def __setitem__(self, key: str, value: Any):
        self.client.set(key, pickle.dumps(
            value, protocol=pickle.HIGHEST_PROTOCOL), ex=config.expireTime)

    def __delitem__(self, key: str):
        self.client.delete(key)

    def __contains__(self, key: str):
        return self.client.exists(key)

    def genSessionId(self) -> str:
        sessionId = config.genSessionId()
        while self.client.get(sessionId):
            sessionId = config.genSessionId()
        return sessionId


def genSessionId() -> str:
    return uuid4().hex


settings = dict(sessionIdGenerator=genSessionId)


class Config(BaseSettings):
    redisURL: str = getenv("REDIS_URL")
    settings: dict = settings
    sessionIdName: str = "OmniPDFSession"
    expireTime: timedelta = timedelta(hours=24)

    def genSessionId(self) -> str:
        return self.settings["sessionIdGenerator"]()


config = Config()


def getSessionStorage() -> Generator:
    storage = SessionStorage()
    yield storage


def getDocList(request: Request, sessionStorage: SessionStorage = Depends(getSessionStorage)):
    sessionId = request.cookies.get(config.sessionIdName, "")
    return sessionStorage[sessionId]


def getSessionId(request: Request):
    sessionId = request.cookies.get(config.sessionIdName, "")
    return sessionId


def setDocList(sessionId: str, session: Any, sessionStorage: SessionStorage):
    sessionStorage[sessionId] = session


def createSession(response: Response, session: Any, sessionStorage: SessionStorage) -> str:
    sessionId = sessionStorage.genSessionId()
    sessionStorage[sessionId] = session
    response.set_cookie(config.sessionIdName, sessionId, httponly=True)
    return sessionId


def deleteSession(response: Response, sessionId: str, sessionStorage: SessionStorage):
    response.set_cookie(config.sessionIdName, sessionId, httponly=True, max_age=0)
    del sessionStorage[sessionId]


def validateSessionId(sessionId: str = Depends(getSessionId), sessionStorage: SessionStorage = Depends(getSessionStorage)) -> bool:
    return sessionId in sessionStorage


def getDocAppend(sessionId: str = Depends(getSessionId), sessionStorage: SessionStorage = Depends(getSessionStorage)) -> Callable[[str], None]:
    def appendDoc(fileName: str):
        sessionData = sessionStorage[sessionId]
        if isinstance(sessionData, list[str]):
            sessionData.append(fileName)
        else:
            sessionData = [fileName]
        sessionStorage[sessionId] = sessionData
    return appendDoc
