# Original code from https://github.com/duyixian1234/fastapi-redis-session
# Updated for package versions listed in requirements.txt

from typing import Any, Callable, Generator
from uuid import uuid4

from fastapi import Depends, Request, Response

import shared_utils.redis


SESSION_COOKIE_NAME: str = "OmniPDFSession"


class SessionStorage(shared_utils.redis.RedisJSONStorage):
    def generate_session_id(self) -> str:
        session_id = uuid4().hex
        while self.client.get(session_id):
            session_id = uuid4().hex
        return session_id


def get_session_storage() -> Generator:
    storage = SessionStorage()
    yield storage


def get_doc_list(
    request: Request, session_storage: SessionStorage = Depends(get_session_storage)
):
    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")
    session_data = session_storage[session_id]
    return session_data if session_data is not None else []


def get_session_id(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")
    return session_id


def set_doc_list(session_id: str, session: Any, session_storage: SessionStorage):
    session_storage[session_id] = session


def create_new_session(
    response: Response, session_storage: SessionStorage = Depends(get_session_storage)
) -> str:
    session_id = session_storage.generate_session_id()
    session_storage[session_id] = []
    response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True)
    return session_id


def delete_session(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
):
    if session_id:
        response.set_cookie(
            SESSION_COOKIE_NAME, session_id, httponly=True, max_age=0
        )
        del session_storage[session_id]


def validate_session_id(
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> bool:
    return session_id in session_storage


def validate_session_doc_pair(
    doc_id: str,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
    valid_session: bool = Depends(validate_session_id),
) -> bool:
    if valid_session:
        return doc_id in session_storage[session_id]
    return False


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


def get_doc_list_remove_function(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> Callable[[str], None]:
    if not validate_session_id(session_id, session_storage):
        session_id = create_new_session(response, session_storage=session_storage)

    def remove_doc(filename: str):
        session_data: list[str] = session_storage[session_id]
        if filename in session_data:
            session_data.remove(filename)
            session_storage[session_id] = session_data

    return remove_doc
