import asyncio
import logging
import os
import time
from datetime import timedelta
from typing import Any, Callable, Dict, Optional, Union

from redis import Redis
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from cache_house.exceptions import RedisNotInitialized
from cache_house.helpers import (
    DEFAULT_NAMESPACE,
    DEFAULT_PREFIX,
    filter_client_kwargs,
    key_builder,
    pickle_decoder,
    pickle_encoder,
)

LOG_LEVEL = os.getenv("CACHE_HOUSE_LOG_LEVEL", logging.INFO)
log = logging.getLogger("cache_house.backends.redis_backend")
log.setLevel(LOG_LEVEL)


def _is_event_loop_error(exc: BaseException) -> bool:
    if not isinstance(exc, RuntimeError):
        return False
    message = str(exc).lower()
    return (
        "event loop is closed" in message
        or "different loop" in message
        or "bound to a different" in message
    )


class RedisCache:
    instance = None

    def __init__(
        self,
        password: Optional[str] = None,
        db: int = 0,
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        fallback_to_memory: bool = True,
        **kwargs,
    ) -> None:
        client_args = {
            "host": host,
            "port": port,
            "db": db,
            "password": password,
            **kwargs,
        }
        self.redis = Redis(**filter_client_kwargs(Redis, client_args))
        # Created lazily per running event loop — asyncio.run() closes loops.
        self._async_client_args = filter_client_kwargs(aioredis.Redis, client_args)
        self.async_redis = None
        self._async_loop_id = None
        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        self.fallback_to_memory = fallback_to_memory
        self._memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        RedisCache.instance = self
        log.info("redis initialized (Redis will handle reconnections automatically)")

    def _create_async_redis(self):
        return aioredis.Redis(**self._async_client_args)

    async def _ensure_async_redis(self):
        """Return an async client bound to the current running event loop."""
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
        if self.async_redis is not None and self._async_loop_id == loop_id:
            return self.async_redis

        log.debug("Creating async Redis client for current event loop")
        self.async_redis = self._create_async_redis()
        self._async_loop_id = loop_id
        return self.async_redis

    def _invalidate_async_redis(self):
        self.async_redis = None
        self._async_loop_id = None

    def _set_memory_cache(self, key: str, val: Any, exp: Union[timedelta, int]):
        """Store value in in-memory cache with expiration"""
        if isinstance(exp, timedelta):
            expiry_time = time.time() + exp.total_seconds()
        else:
            expiry_time = time.time() + exp
        self._memory_cache[key] = (val, expiry_time)
        # Clean up expired entries periodically
        if len(self._memory_cache) > 1000:
            self._cleanup_memory_cache()

    def _get_memory_cache(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache if not expired"""
        if key in self._memory_cache:
            val, expiry_time = self._memory_cache[key]
            if time.time() < expiry_time:
                return val
            else:
                # Expired, remove it
                del self._memory_cache[key]
        return None

    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self._memory_cache.items()
            if current_time >= expiry_time
        ]
        for key in expired_keys:
            del self._memory_cache[key]

    def _get_from_memory(self, key: str, decode: Callable[..., Any]):
        if not self.fallback_to_memory:
            return None
        try:
            encoded_val = self._get_memory_cache(key)
            if encoded_val:
                log.debug(f"Retrieved key '{key}' from memory cache (Redis unavailable)")
                return decode(encoded_val)
        except Exception as mem_error:
            log.error(f"Failed to retrieve from memory cache: {mem_error}")
        return None

    def _set_in_memory(self, key: str, encoded_val: Any, exp: Union[timedelta, int]):
        if not self.fallback_to_memory:
            return
        try:
            self._set_memory_cache(key, encoded_val, exp)
            log.debug(f"Stored key '{key}' in memory cache (Redis unavailable)")
        except Exception as mem_error:
            log.error(f"Failed to store in memory cache: {mem_error}")

    def set_key(
        self,
        key,
        val,
        exp: Union[timedelta, int],
        encoder: Optional[Callable[..., Any]] = None,
    ):
        """Set key in Redis with fallback to memory cache"""
        encode = encoder or self.encoder
        encoded_val = encode(val)

        if self.redis is None:
            self._set_in_memory(key, encoded_val, exp)
            return

        # Try Redis first - Redis client handles reconnection automatically
        try:
            self.redis.set(key, encoded_val, ex=exp)
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis set_key failed: {e}")
            self._set_in_memory(key, encoded_val, exp)

    def get_key(self, key: str, decoder: Optional[Callable[..., Any]] = None):
        """Get key from Redis with fallback to memory cache"""
        decode = decoder or self.decoder

        if self.redis is None:
            return self._get_from_memory(key, decode)

        # Try Redis first - Redis client handles reconnection automatically
        try:
            val = self.redis.get(key)
            if val:
                return decode(val)
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis get_key failed: {e}")
            return self._get_from_memory(key, decode)

        return None

    async def aset_key(
        self,
        key,
        val,
        exp: Union[timedelta, int],
        encoder: Optional[Callable[..., Any]] = None,
    ):
        """Async set key in Redis with fallback to memory cache"""
        encode = encoder or self.encoder
        encoded_val = encode(val)

        try:
            client = await self._ensure_async_redis()
        except Exception as e:
            log.warning(f"Async Redis client unavailable: {e}")
            self._set_in_memory(key, encoded_val, exp)
            return

        try:
            await client.set(key, encoded_val, ex=exp)
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis aset_key failed: {e}")
            self._set_in_memory(key, encoded_val, exp)
        except RuntimeError as e:
            if not _is_event_loop_error(e):
                raise
            log.debug(f"Async Redis loop stale on set; recreating client: {e}")
            self._invalidate_async_redis()
            try:
                client = await self._ensure_async_redis()
                await client.set(key, encoded_val, ex=exp)
            except Exception as retry_error:
                log.warning(f"Redis aset_key failed after loop reset: {retry_error}")
                self._set_in_memory(key, encoded_val, exp)

    async def aget_key(self, key: str, decoder: Optional[Callable[..., Any]] = None):
        """Async get key from Redis with fallback to memory cache"""
        decode = decoder or self.decoder

        try:
            client = await self._ensure_async_redis()
        except Exception as e:
            log.warning(f"Async Redis client unavailable: {e}")
            return self._get_from_memory(key, decode)

        try:
            val = await client.get(key)
            if val:
                return decode(val)
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis aget_key failed: {e}")
            return self._get_from_memory(key, decode)
        except RuntimeError as e:
            if not _is_event_loop_error(e):
                raise
            log.debug(f"Async Redis loop stale on get; recreating client: {e}")
            self._invalidate_async_redis()
            try:
                client = await self._ensure_async_redis()
                val = await client.get(key)
                if val:
                    return decode(val)
            except Exception as retry_error:
                log.warning(f"Redis aget_key failed after loop reset: {retry_error}")
                return self._get_from_memory(key, decode)

        return None

    @classmethod
    def get_instance(cls):
        if cls.instance:
            return cls.instance
        raise RedisNotInitialized("RedisCache", "You must initialize Redis before using the cache backend")

    @classmethod
    def clear_keys(cls, pattern: str):
        """Clear keys matching pattern, with error handling"""
        if not cls.instance:
            log.warning("RedisCache instance not available")
            return False

        ns_keys = f"{pattern}*"

        if cls.instance.redis is None:
            if cls.instance.fallback_to_memory:
                try:
                    keys_to_delete = [
                        key for key in cls.instance._memory_cache.keys()
                        if key.startswith(pattern)
                    ]
                    for key in keys_to_delete:
                        del cls.instance._memory_cache[key]
                    log.debug(f"Cleared {len(keys_to_delete)} keys from memory cache")
                    return True
                except Exception as mem_error:
                    log.error(f"Failed to clear memory cache: {mem_error}")
            return False

        # Try Redis first - Redis client handles reconnection automatically
        try:
            for key in cls.instance.redis.scan_iter(match=ns_keys):
                if key:
                    cls.instance.redis.delete(key)
            return True
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis clear_keys failed: {e}")
            # Fallback: clear from memory cache
            if cls.instance.fallback_to_memory:
                try:
                    keys_to_delete = [
                        key for key in cls.instance._memory_cache.keys()
                        if key.startswith(pattern)
                    ]
                    for key in keys_to_delete:
                        del cls.instance._memory_cache[key]
                    log.debug(f"Cleared {len(keys_to_delete)} keys from memory cache")
                    return True
                except Exception as mem_error:
                    log.error(f"Failed to clear memory cache: {mem_error}")

        return False

    @classmethod
    def init(
        cls,
        password: Optional[str] = None,
        db: int = 0,
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        fallback_to_memory: bool = True,
        **kwargs,
    ):
        if not cls.instance:
            cls(
                host=host,
                port=port,
                db=db,
                password=password,
                encoder=encoder,
                decoder=decoder,
                namespace=namespace,
                key_prefix=key_prefix,
                key_builder=key_builder,
                fallback_to_memory=fallback_to_memory,
                **kwargs,
            )
