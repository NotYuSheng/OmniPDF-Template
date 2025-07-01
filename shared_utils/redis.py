# Original code from https://github.com/duyixian1234/fastapi-redis-session
# Updated for package versions listed in requirements.txt

from os import getenv
from datetime import timedelta
from typing import Any, Generator
import logging
import json

from pydantic_settings import BaseSettings
from fastapi import HTTPException
from redis import Redis


logger = logging.getLogger(__name__)


class Config(BaseSettings):
    redis_url: str = getenv("REDIS_URL")
    session_id_name: str = "OmniPDFSession"
    expire_time: timedelta = timedelta(hours=24)


config = Config()


# Stores the data as string
class RedisStringStorage:
    def __init__(self):
        self.client = Redis.from_url(config.redis_url)

    def __getitem__(self, key: str):
        return self.client.get(key)

    def __setitem__(self, key: str, value: str):
        self.client.set(
            key,
            value,
            ex=config.expire_time,
        )

    def __delitem__(self, key: str):
        self.client.delete(key)

    def __contains__(self, key: str):
        return self.client.exists(key)


# Stores the data as string using json
class RedisJSONStorage(RedisStringStorage):
    def __init__(self):
        super().__init__()

    def __getitem__(self, key: str):
        raw = self.client.get(key)
        if not raw:
            logger.info(f"Trying to load empty key {key}.")
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON data for {key}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Unable to load session data from memory. Please start a new session.",
            )

    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key, json.dumps(value))

    def __delitem__(self, key: str):
        self.client.delete(key)

    def __contains__(self, key: str):
        return self.client.exists(key)


class RedisSetStorage:
    def __init__(self):
        self.client = Redis.from_url(config.redis_url)

    def __getitem__(self, key: str) -> set[str]:
        return self.client.smembers(key)

    def __delitem__(self, key: str):
        self.client.delete(key)

    def __contains__(self, key: str):
        return self.client.exists(key)

    def add(self, key: str, value: str):
        self.client.sadd(key, value)
        self.client.expire(key, config.expire_time)

    def contains(self, key: str, value: str) -> bool:
        return self.client.sismember(key, value)

    def clear(self, key: str):
        self.__delitem__(key)

    def remove(self, key: str, value: str):
        self.client.srem(key, value)
        self.client.expire(key, config.expire_time)


def get_json_storage() -> Generator:
    storage = RedisJSONStorage()
    yield storage


def get_set_storage() -> Generator:
    service_cache = RedisSetStorage()
    yield service_cache


def get_string_storage() -> Generator:
    service_cache = RedisStringStorage()
    yield service_cache
