import inspect
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Union

from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache
from cache_house.helpers import DEFAULT_EXPIRE_TIME

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def cache(
    expire: Union[timedelta, int] = DEFAULT_EXPIRE_TIME,
    namespace: str = None,
    key_prefix: str = None,
    key_builder: Callable[..., Any] = None,
    encoder: Callable[..., Any] = None,
    decoder: Callable[..., Any] = None
) -> Callable:
    """Decorator for caching results"""

    cache_instance = None

    def cache_wrap(f: Callable[..., Any]):

        @wraps(f)
        async def async_wrapper(*args, **kwargs):
            nonlocal namespace
            nonlocal encoder
            nonlocal decoder
            if RedisCache.instance:
                cache_instance = RedisCache.get_instance()
            elif RedisClusterCache.instance:
                cache_instance = RedisClusterCache.get_instance()
            if cache_instance is not None:
                key_generator = key_builder or cache_instance.key_builder
                namespace = namespace or cache_instance.namespace
                prefix = key_prefix or cache_instance.key_prefix
                encoder = encoder or cache_instance.encoder
                decoder = decoder or cache_instance.decoder
            if cache_instance is None:
                return await f(*args, **kwargs)

            key = key_generator(
                f.__module__,
                f.__name__,
                args,
                kwargs,
                namespace=namespace,
                prefix=prefix,
            )
            cached_data = cache_instance.get_key(key)
            if cached_data:
                log.info("data exist in cache")
                log.info("return data from cache")
                return decoder(cached_data)
            result = await f(*args, **kwargs)
            cache_instance.set_key(key, encoder(result), expire)
            log.info("set result in cache")
            return result

        @wraps(f)
        def wrapper(*args, **kwargs):
            nonlocal namespace
            nonlocal encoder
            nonlocal decoder
            if RedisCache.instance:
                cache_instance = RedisCache.get_instance()
            elif RedisClusterCache.instance:
                cache_instance = RedisClusterCache.get_instance()
            if cache_instance is not None:
                key_generator = key_builder or cache_instance.key_builder
                namespace = namespace or cache_instance.namespace
                prefix = key_prefix or cache_instance.key_prefix
                encoder = encoder or cache_instance.encoder
                decoder = decoder or cache_instance.decoder
            if cache_instance is None:
                return f(*args, **kwargs)
            key = key_generator(
                f.__module__,
                f.__name__,
                args,
                kwargs,
                namespace=namespace,
                prefix=prefix,
            )
            cached_data = cache_instance.get_key(key)
            if cached_data:
                log.info("data exist in cache")
                log.info("return data from cache")
                return decoder(cached_data)
            result = f(*args, **kwargs)
            cache_instance.set_key(key, encoder(result), expire)
            log.info("set result in cache")
            return result

        return async_wrapper if inspect.iscoroutinefunction(f) else wrapper

    return cache_wrap
