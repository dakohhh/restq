from typing import Any
from redis import Redis, from_url as sync_redis_from_url
from redis.asyncio import Redis as AsyncRedis, from_url as async_redis_from_url


def get_redis_async_client(url: str, *args: Any, **kwargs: Any) -> AsyncRedis:
    redis = async_redis_from_url(url, *args, **kwargs) # type: ignore

    return redis #type: ignore

def get_redis_sync_client(url: str, *args: Any, **kwargs: Any) -> Redis:
    redis = sync_redis_from_url(url, *args, **kwargs) # type: ignore

    return redis #type: ignore