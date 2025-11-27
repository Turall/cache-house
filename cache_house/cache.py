import inspect
import logging
import os
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Union

from cache_house.backends import RedisFactory
from cache_house.helpers import DEFAULT_EXPIRE_TIME

LOG_LEVEL = os.getenv("CACHE_HOUSE_LOG_LEVEL", logging.INFO)
log = logging.getLogger("cache_house.cache")
log.setLevel(LOG_LEVEL)

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

            cache_instance = RedisFactory.get_instance()

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
            try:
                cached_data = cache_instance.get_key(key)
                if cached_data:
                    log.debug("data exist in cache")
                    log.debug("return data from cache")
                    return decoder(cached_data)
            except Exception as e:
                log.warning(f"Error retrieving from cache: {e}. Proceeding without cache.")
            
            result = await f(*args, **kwargs)
            try:
                cache_instance.set_key(key, encoder(result), expire)
                log.debug("set result in cache")
            except Exception as e:
                log.warning(f"Error setting cache: {e}. Result returned without caching.")
            return result

        @wraps(f)
        def wrapper(*args, **kwargs):
            nonlocal namespace
            nonlocal encoder
            nonlocal decoder
            
            cache_instance = RedisFactory.get_instance()
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
            try:
                cached_data = cache_instance.get_key(key)
                if cached_data:
                    log.info("data exist in cache")
                    log.info("return data from cache")
                    return decoder(cached_data)
            except Exception as e:
                log.warning(f"Error retrieving from cache: {e}. Proceeding without cache.")
            
            result = f(*args, **kwargs)
            try:
                cache_instance.set_key(key, encoder(result), expire)
                log.info("set result in cache")
            except Exception as e:
                log.warning(f"Error setting cache: {e}. Result returned without caching.")
            return result

        return async_wrapper if inspect.iscoroutinefunction(f) else wrapper

    return cache_wrap
