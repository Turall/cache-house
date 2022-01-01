import inspect
from typing import Callable, Any
from functools import wraps
from fast_cache.helpers import key_builder
from fast_cache.backends.redis_backend import RedisCache

def cache(f: Callable[..., Any]):
    @wraps(f)
    async def async_wrapper(*args, **kwargs):
        key = key_builder(f.__module__, f.__name__, args, kwargs)
        cache_instance = RedisCache.get_instance()
        cached_data = cache_instance.get_key(key)
        if cached_data:
            return cached_data
        return await f(*args, **kwargs)

    @wraps(f)
    def wrapper(*args, **kwargs):
        key = key_builder(f.__module__, f.__name__, args, kwargs)
        cache_instance = RedisCache.get_instance()
        cached_data = cache_instance.get_key(key)
        if cached_data:
            return cached_data
        result =  f(*args, **kwargs)
        cache_instance.set_key(key,result,5)
        return result
        

    return async_wrapper if inspect.iscoroutinefunction(f) else wrapper
