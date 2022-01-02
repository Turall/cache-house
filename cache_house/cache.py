import inspect
import logging
from datetime import timedelta
from typing import Callable, Any, Union
from functools import wraps
from cache_house.helpers import DEFAULT_EXPIRE, key_builder
from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache


log = logging.getLogger(__name__)



def cache(
    expire: Union[timedelta, int] = DEFAULT_EXPIRE,
    namespace: str = "main",
    key_prefix="cachehouse",
    key_builder: Callable[..., Any] = key_builder,
) -> Callable:
    def cache_wrap(f: Callable[..., Any]):
        @wraps(f)
        async def async_wrapper(*args, **kwargs):
            key = key_builder(
                f.__module__, f.__name__, args, kwargs, namespace=namespace, prefix=key_prefix
            )
            if RedisCache.instance:
                cache_instance = RedisCache.get_instance()
            elif RedisClusterCache.instance:
                cache_instance = RedisClusterCache.get_instance()
            else:
                raise Exception("You mus be initialize redis first")
            cached_data = cache_instance.get_key(key)
            if cached_data:
                log.info("data exist in cache")
                log.info("return data from cache")
                return cached_data
            result = await f(*args, **kwargs)
            cache_instance.set_key(key, result, expire)
            log.info("set result in cache")
            return result

        @wraps(f)
        def wrapper(*args, **kwargs):
            key = key_builder(f.__module__, f.__name__, args, kwargs)
            cache_instance = RedisCache.get_instance()
            cached_data = cache_instance.get_key(key)
            if cached_data:
                log.info("find data in cache")
                log.info("return data from cache")
                return cached_data
            result = f(*args, **kwargs)
            cache_instance.set_key(key, result, expire)
            log.info("set result in cache")

            return result

        return async_wrapper if inspect.iscoroutinefunction(f) else wrapper

    return cache_wrap
