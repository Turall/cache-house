import logging
import os
from typing import Any, Callable, Dict

from redis.cluster import RedisCluster
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from cache_house.backends.redis_backend import RedisCache
from cache_house.helpers import (
    DEFAULT_NAMESPACE,
    DEFAULT_PREFIX,
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
        host="localhost",
        port=6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        startup_nodes=None,
        cluster_error_retry_attempts: int = 3,
        require_full_coverage: bool = True,
        skip_full_coverage_check: bool = False,
        reinitialize_steps: int = 10,
        read_from_replicas: bool = False,
        url: Any = None,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        fallback_to_memory: bool = True,
        **kwargs,
    ) -> None:
        self.host = host
        self.port = port
        self.startup_nodes = startup_nodes
        self.cluster_error_retry_attempts = cluster_error_retry_attempts
        self.require_full_coverage = require_full_coverage
        self.skip_full_coverage_check = skip_full_coverage_check
        self.reinitialize_steps = reinitialize_steps
        self.read_from_replicas = read_from_replicas
        self.url = url
        self.cluster_kwargs = kwargs
        
        try:
            self.redis = RedisCluster(
                host=host,
                port=port,
                startup_nodes=startup_nodes,
                cluster_error_retry_attempts=cluster_error_retry_attempts,
                require_full_coverage=require_full_coverage,
                skip_full_coverage_check=skip_full_coverage_check,
                reinitialize_steps=reinitialize_steps,
                read_from_replicas=read_from_replicas,
                url=url,
                **kwargs,
            )
            log.info("redis cluster initialized (Redis will handle reconnections automatically)")
        except (ConnectionError, TimeoutError, RedisError) as e:
            log.warning(f"Redis cluster connection failed during initialization: {e}")
            log.warning("Falling back to in-memory cache. Redis operations will be retried automatically.")
            self.redis = None
        
        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        self.fallback_to_memory = fallback_to_memory
        self._memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        RedisClusterCache.instance = self

    @classmethod
    def init(
        cls,
        host="localhost",
        port=6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        startup_nodes=None,
        cluster_error_retry_attempts: int = 3,
        require_full_coverage: bool = True,
        skip_full_coverage_check: bool = False,
        reinitialize_steps: int = 10,
        read_from_replicas: bool = False,
        url: Any = None,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        **kwargs,
    ):
        if not cls.instance:
            cls(
                host=host,
                port=port,
                startup_nodes=startup_nodes,
                cluster_error_retry_attempts=cluster_error_retry_attempts,
                require_full_coverage=require_full_coverage,
                skip_full_coverage_check=skip_full_coverage_check,
                reinitialize_steps=reinitialize_steps,
                read_from_replicas=read_from_replicas,
                url=url,
                encoder=encoder,
                decoder=decoder,
                namespace=namespace,
                key_prefix=key_prefix,
                key_builder=key_builder,
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
            for key in cls.instance.redis.scan_iter(match=ns_keys, count=batch_size, target_nodes=RedisCluster.ALL_NODES):
                log.info(key)
                keys.append(key)
                if len(keys) >= batch_size:
                    cls.instance.redis.delete(*keys)
                    keys = []
                if len(keys) > 0:
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