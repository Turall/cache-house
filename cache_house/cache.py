import inspect
from datetime import timedelta
from typing import Callable, Any, Union
from functools import wraps
from cache_house.helpers import DEFAULT_EXPIRE, key_builder
from cache_house.backends.redis_backend import RedisCache


def log_class(expire: Union[timedelta, int] = DEFAULT_EXPIRE) -> Callable:
    def cache(f: Callable[..., Any]):
        @wraps(f)
        async def async_wrapper(*args, **kwargs):
            key = key_builder(f.__module__, f.__name__, args, kwargs)
            cache_instance = RedisCache.get_instance()
            cached_data = cache_instance.get_key(key)
            if cached_data:
                return cached_data
            result =  await f(*args, **kwargs)
            cache_instance.set_key(key, result, expire)
            return result

        @wraps(f)
        def wrapper(*args, **kwargs):
            key = key_builder(f.__module__, f.__name__, args, kwargs)
            cache_instance = RedisCache.get_instance()
            cached_data = cache_instance.get_key(key)
            if cached_data:
                return cached_data
            result = f(*args, **kwargs)
            cache_instance.set_key(key, result, expire)
            return result

        return async_wrapper if inspect.iscoroutinefunction(f) else wrapper

    return cache
