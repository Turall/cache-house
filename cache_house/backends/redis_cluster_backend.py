import logging
import os
import warnings
from typing import Any, Callable, Dict, Optional

from redis.asyncio.cluster import RedisCluster as AsyncRedisCluster
from redis.cluster import RedisCluster
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from cache_house.backends.redis_backend import RedisCache
from cache_house.helpers import (
    DEFAULT_NAMESPACE,
    DEFAULT_PREFIX,
    filter_client_kwargs,
    key_builder,
    pickle_decoder,
    pickle_encoder,
)

LOG_LEVEL = os.getenv("CACHE_HOUSE_LOG_LEVEL", logging.INFO)
log = logging.getLogger("cache_house.backends.redis_cluster_backend")
log.setLevel(LOG_LEVEL)


class RedisClusterCache(RedisCache):
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
        *,
        startup_nodes=None,
        cluster_error_retry_attempts: int = 10,
        require_full_coverage: bool = True,
        reinitialize_steps: int = 5,
        read_from_replicas: bool = False,
        url: Any = None,
        **kwargs,
    ) -> None:
        # db is unused by Redis Cluster; kept for RedisCache signature compatibility.
        _ = db

        # Removed in redis-py; map the old flag onto require_full_coverage.
        skip_full_coverage_check = kwargs.pop("skip_full_coverage_check", None)
        if skip_full_coverage_check:
            warnings.warn(
                "skip_full_coverage_check is removed in redis-py; "
                "use require_full_coverage=False instead",
                DeprecationWarning,
                stacklevel=2,
            )
            require_full_coverage = False

        self.host = host
        self.port = port
        self.startup_nodes = startup_nodes
        self.cluster_error_retry_attempts = cluster_error_retry_attempts
        self.require_full_coverage = require_full_coverage
        self.reinitialize_steps = reinitialize_steps
        self.read_from_replicas = read_from_replicas
        self.url = url
        self.cluster_kwargs = kwargs

        if password is not None and "password" not in kwargs:
            kwargs = {**kwargs, "password": password}

        shared_args = dict(
            host=host,
            port=port,
            startup_nodes=startup_nodes,
            cluster_error_retry_attempts=cluster_error_retry_attempts,
            require_full_coverage=require_full_coverage,
            reinitialize_steps=reinitialize_steps,
            read_from_replicas=read_from_replicas,
            **kwargs,
        )

        self.redis = None
        self.async_redis = None
        self._async_loop_id = None
        self._async_client_args = filter_client_kwargs(AsyncRedisCluster, shared_args)
        try:
            sync_args = filter_client_kwargs(RedisCluster, {**shared_args, "url": url})
            self.redis = RedisCluster(**sync_args)
            log.info("redis cluster initialized (Redis will handle reconnections automatically)")
        except (ConnectionError, TimeoutError, RedisError, TypeError) as e:
            log.warning(f"Redis cluster connection failed during initialization: {e}")
            log.warning("Falling back to in-memory cache for sync operations.")

        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        self.fallback_to_memory = fallback_to_memory
        self._memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        RedisClusterCache.instance = self

    def _create_async_redis(self):
        return AsyncRedisCluster(**self._async_client_args)

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
        *,
        startup_nodes=None,
        cluster_error_retry_attempts: int = 10,
        require_full_coverage: bool = True,
        reinitialize_steps: int = 5,
        read_from_replicas: bool = False,
        url: Any = None,
        **kwargs,
    ):
        if not cls.instance:
            cls(
                password=password,
                db=db,
                host=host,
                port=port,
                encoder=encoder,
                decoder=decoder,
                namespace=namespace,
                key_prefix=key_prefix,
                key_builder=key_builder,
                fallback_to_memory=fallback_to_memory,
                startup_nodes=startup_nodes,
                cluster_error_retry_attempts=cluster_error_retry_attempts,
                require_full_coverage=require_full_coverage,
                reinitialize_steps=reinitialize_steps,
                read_from_replicas=read_from_replicas,
                url=url,
                **kwargs,
            )

    @classmethod
    def clear_keys(cls, pattern: str):
        """Clear keys matching pattern, with error handling"""
        if not cls.instance:
            log.warning("RedisClusterCache instance not available")
            return False

        if cls.instance.redis is None:
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

        ns_keys = f"{pattern}*"

        # Try Redis cluster first - Redis client handles reconnection automatically
        try:
            keys = []
            batch_size = 300
            for key in cls.instance.redis.scan_iter(
                match=ns_keys,
                count=batch_size,
                target_nodes=RedisCluster.ALL_NODES,
            ):
                log.info(key)
                keys.append(key)
                if len(keys) >= batch_size:
                    cls.instance.redis.delete(*keys)
                    keys = []
            if keys:
                cls.instance.redis.delete(*keys)
            return True
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis cluster clear_keys failed: {e}")
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
