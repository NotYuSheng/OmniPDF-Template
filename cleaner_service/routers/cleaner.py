from fastapi import Depends, APIRouter
from shared_utils.redis import get_string_storage
from shared_utils.ttl_utils import REDIS_FLAG, S3_FLAG, CHROMA_FLAG, key_with_prefix


router = APIRouter(prefix="/cleaner", tags=["cleaner"])


@router.post("/redis")
async def set_redis_expiry_flag(
    key: str,
    TTL: int,
    redis_string_storage=Depends(get_string_storage),
):
    redis_string_storage[key_with_prefix(REDIS_FLAG, key)] = 1
    return


@router.post("/s3")
async def set_s3_expiry_flag(
    key: str,
    TTL: int,
    redis_string_storage=Depends(get_string_storage)
):
    redis_string_storage[key_with_prefix(S3_FLAG, key)] = 1
    return


@router.post("/chroma")
async def set_chromadb_expiry_flag(
    key: str,
    TTL: int,
    redis_string_storage=Depends(get_string_storage)
):
    redis_string_storage[key_with_prefix(CHROMA_FLAG, key)] = 1
    return