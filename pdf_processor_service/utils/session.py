# Original code from https://github.com/duyixian1234/fastapi-redis-session
# Updated for package versions listed in requirements.txt

from datetime import timedelta
from typing import Callable, Generator
from uuid import uuid4

from fastapi import Depends, Request, Response

import shared_utils.redis


SESSION_COOKIE_NAME: str = "OmniPDFSession"
SESSION_REDIS_PREFIX = "Session_Files:"
SESSION_FLAG_PREFIX = "SessionHeader:"


class SessionStorage(shared_utils.redis.RedisSetStorage):
    def __init__(self, redis_client=None, prefix=SESSION_REDIS_PREFIX):
        super().__init__(redis_client, prefix, default_expiry=None)
        self.flag_expiry = timedelta(days=1)

    def generate_session2(self) -> str:
        session_id = uuid4().hex
        while session_id in self:
            session_id = uuid4().hex
        # create an empty list
        self.add(session_id, "")
        return session_id

    def generate_session(self) -> str:
        session_id = uuid4().hex
        while not self.client.set(SESSION_FLAG_PREFIX+ SESSION_REDIS_PREFIX + session_id, 1, ex= self.flag_expiry, nx=True):
            session_id = uuid4().hex
        return session_id
    
    def __delitem__(self, key):
        self.client.delete(SESSION_FLAG_PREFIX+ SESSION_REDIS_PREFIX + key)
    
    def __contains__(self, key):
        return self.client.exists(SESSION_FLAG_PREFIX+ SESSION_REDIS_PREFIX + key)
    
    def add(self, key, value):
        self.pipeline.expire(SESSION_FLAG_PREFIX+ SESSION_REDIS_PREFIX + key, self.flag_expiry)
        return super().add(key, value)
    
    def remove(self, key, value):
        self.pipeline.expire(SESSION_FLAG_PREFIX + key, self.flag_expiry)
        return super().remove(key, value)

def get_session_storage() -> Generator[SessionStorage]:
    storage = SessionStorage()
    yield storage


def get_session_id(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")
    return session_id


def create_new_session(
    response: Response, session_storage: SessionStorage = Depends(get_session_storage)
) -> str:
    session_id = session_storage.generate_session()
    response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True)
    return session_id


def delete_session(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
):
    if session_id:
        response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True, max_age=0)
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
        return session_storage.contains(session_id, doc_id)
        # return doc_id in session_storage[session_id]
    return False


def get_doc_list_append_function(
    response: Response,
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> Callable[[str], None]:
    if not validate_session_id(session_id, session_storage):
        session_id = create_new_session(response, session_storage=session_storage)

    def append_doc(filename: str):
        session_storage.add(session_id, filename)

    return append_doc


def get_doc_list_remove_function(
    session_id: str = Depends(get_session_id),
    session_storage: SessionStorage = Depends(get_session_storage),
) -> Callable[[str], None]:
    def remove_doc(filename: str):
        session_storage.remove(session_id, filename)

    return remove_doc
