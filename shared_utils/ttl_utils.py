from http import client

TTL_HOST = "cleaner_service"
TTL_PORT = 8000
SEPERATOR = ":"

REDIS_FLAG = "RedisKey"
S3_FLAG = "S3Key"
CHROMA_FLAG = "ChromaDBKey"


def key_with_prefix(prefix: str, key: str):
    return prefix + SEPERATOR + key


def create_redis_ttl(key: str, ttl: int):
    conn = client.HTTPConnection(TTL_HOST, TTL_PORT)
    conn.request("POST", "/cleaner/redis", body={"key": key, "ttl": ttl})
    response = conn.getresponse()
    return response.status == 200


def create_s3_ttl(key: str, ttl: int):
    conn = client.HTTPConnection(TTL_HOST, TTL_PORT)
    conn.request("POST", "/cleaner/s3", body={"key": key, "ttl": ttl})
    response = conn.getresponse()
    return response.status == 200


def create_chroma_ttl(key: str, ttl: int):
    conn = client.HTTPConnection(TTL_HOST, TTL_PORT)
    conn.request("POST", "/cleaner/chroma", body={"key": key, "ttl": ttl})
    response = conn.getresponse()
    return response.status == 200