# Original code from https://github.com/duyixian1234/fastapi-redis-session
# Updated for package versions listed in requirements.txt

from os import getenv
from datetime import timedelta
from typing import Any, Generator
import logging
import json

from pydantic_settings import BaseSettings
from redis import Redis


logger = logging.getLogger(__name__)


class Config(BaseSettings):
    redis_url: str = getenv("REDIS_URL")
    session_id_name: str = "OmniPDFSession"
    expire_time: timedelta = timedelta(hours=24)


config = Config()


class RedisBase:
    def __init__(self, redis_client=None, prefix="", default_expiry: timedelta | None = config.expire_time):
        self.client = (
            redis_client if redis_client else Redis.from_url(config.redis_url)
        )
        self.prefix = prefix
        self.default_expiry = default_expiry

    def __delitem__(self, key: str):
        self.client.delete(self.prefix + key)

    def __contains__(self, key: str):
        return self.client.exists(self.prefix + key)


# Stores the data as string
class RedisStringStorage(RedisBase):
    def __getitem__(self, key: str):
        # return self.client.get(self.prefix + key)
        return self.client.getex(self.prefix + key, self.default_expiry)

    def __setitem__(self, key: str, value: str):
        self.client.set(
            self.prefix + key,
            value,
            ex=self.default_expiry,
        )


# Stores the data as string using json
class RedisJSONStorage(RedisStringStorage):
    def __getitem__(self, key: str):
        raw = super().__getitem__(key)
        if not raw:
            logger.info(f"Trying to load empty key {key}.")
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON data for {key}: {e}")
            raise e

    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key, json.dumps(value))


class RedisSetStorage(RedisBase):
    def __init__(self, redis_client=None, prefix="", default_expiry = config.expire_time):
        super().__init__(redis_client, prefix, default_expiry)
        self.pipeline = self.client.pipeline()

    def __getitem__(self, key: str) -> set[str]:
        if self.default_expiry is not None:
            self.pipeline.expire(self.prefix + key, self.default_expiry)
        self.pipeline.smembers(self.prefix + key)
        members = self.pipeline.execute()[-1]
        return members

    def add(self, key: str, value: str):
        self.pipeline.sadd(self.prefix + key, value)
        if self.default_expiry is not None:
            self.pipeline.expire(self.prefix + key, self.default_expiry)
        self.pipeline.execute()

    def contains(self, key: str, value: str) -> bool:
        return self.client.sismember(self.prefix + key, value)

    def remove(self, key: str, value: str):
        self.pipeline.srem(self.prefix + key, value)
        if self.default_expiry is not None:
            self.pipeline.expire(self.prefix + key, self.default_expiry)
        self.pipeline.execute()



def get_json_storage() -> Generator:
    storage = RedisJSONStorage()
    yield storage


def get_set_storage() -> Generator:
    service_cache = RedisSetStorage()
    yield service_cache


def get_string_storage() -> Generator:
    service_cache = RedisStringStorage()
    yield service_cache
