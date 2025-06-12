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
from typing import Any

from redis import Redis


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


def basicConfig(
    redisURL: Optional[str] = "",
    sessionIdName: Optional[str] = "",
    sessionIdGenerator: Optional[Callable[[], str]] = None,
    expireTime: Optional[timedelta] = None,
):
    if redisURL:
        config.redisURL = redisURL
    if sessionIdName:
        config.sessionIdName = sessionIdName
    if sessionIdGenerator:
        config.settings["sessionIdGenerator"] = sessionIdGenerator
    if expireTime:
        config.expireTime = expireTime


def getSessionStorage() -> Generator:
    storage = SessionStorage()
    yield storage


def getSession(request: Request, sessionStorage: SessionStorage = Depends(getSessionStorage)):
    sessionId = request.cookies.get(config.sessionIdName, "")
    return sessionStorage[sessionId]


def getSessionId(request: Request):
    sessionId = request.cookies.get(config.sessionIdName, "")
    return sessionId


def setSession(sessionId: str, session: Any, sessionStorage: SessionStorage) -> str:
    sessionStorage[sessionId] = session


def createSession(response: Response, session: Any, sessionStorage: SessionStorage) -> str:
    sessionId = sessionStorage.genSessionId()
    sessionStorage[sessionId] = session
    return sessionId


def deleteSession(sessionId: str, sessionStorage: SessionStorage):
    del sessionStorage[sessionId]
