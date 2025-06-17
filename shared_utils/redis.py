# Original code from https://github.com/duyixian1234/fastapi-redis-session
# Updated for package versions listed in requirements.txt

from os import getenv
from datetime import timedelta
from typing import Any, Callable, Generator
from uuid import uuid4

from pydantic_settings import BaseSettings
from fastapi import Depends, Request, Response
import json
from redis import Redis

# Stores the data as string using json


class SessionStorage:
    def __init__(self):
        self.client = Redis.from_url(config.redis_url)

    def __getitem__(self, key: str):
        raw = self.client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def __setitem__(self, key: str, value: Any):
        self.client.set(
            key,
            json.dumps(value),
            ex=config.expireTime,
        )

    def __delitem__(self, key: str):
        self.client.delete(key)

    def __contains__(self, key: str):
        return self.client.exists(key)

    def generate_session_id(self) -> str:
        session_id = config.generate_session_id()
        while self.client.get(session_id):
            session_id = config.generate_session_id()
        return session_id


def generate_session_id() -> str:
    return uuid4().hex


settings = dict(session_id_generator=generate_session_id)


class Config(BaseSettings):
    redis_url: str = getenv("REDIS_URL")
    settings: dict = settings
    session_id_name: str = "OmniPDFSession"
    expireTime: timedelta = timedelta(hours=24)

    def generate_session_id(self) -> str:
        return self.settings["session_id_generator"]()


config = Config()


def get_session_storage() -> Generator:
    storage = SessionStorage()
    yield storage


def get_doc_list(
    request: Request, session_storage: SessionStorage = Depends(get_session_storage)
):
    session_id = request.cookies.get(config.session_id_name, "")
    session_data = session_storage[session_id]
    return session_data if session_data is not None else []


def get_session_id(request: Request):
    session_id = request.cookies.get(config.session_id_name, "")
    return session_id


def set_doc_list(session_id: str, session: Any, session_storage: SessionStorage):
    session_storage[session_id] = session


def create_new_session(
    response: Response, session_storage: SessionStorage = Depends(get_session_storage)
) -> str:
    session_id = session_storage.generate_session_id()
    session_storage[session_id] = []
    response.set_cookie(config.session_id_name, session_id, httponly=True)
    return session_id


def delete_session(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
):
    if session_id:
        response.set_cookie(config.session_id_name, session_id, httponly=True, max_age=0)
        del session_storage[session_id]


def validate_session_id(
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> bool:
    return session_id in session_storage


def get_doc_list_append_function(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> Callable[[str], None]:
    if not validate_session_id(session_id, session_storage):
        session_id = create_new_session(response, session_storage=session_storage)

    def append_doc(filename: str):
        session_data = session_storage[session_id]
        if isinstance(session_data, list):
            session_data.append(filename)
        else:
            session_data = [filename]
        session_storage[session_id] = session_data

    return append_doc
