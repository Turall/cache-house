import logging
from typing import Callable, Any
from redis.cluster import RedisCluster
from cache_house.backends.redis_backend import RedisCache
from cache_house.helpers import (
    pickle_encoder,
    pickle_decoder,
    DEFAULT_PREFIX,
    DEFAULT_NAMESPACE,
    key_builder,
)


log = logging.getLogger(__name__)


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
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        **kwargs,
    ) -> None:
        self.redis = RedisCluster(
            host,
            port,
            startup_nodes,
            cluster_error_retry_attempts,
            require_full_coverage,
            skip_full_coverage_check,
            reinitialize_steps,
            read_from_replicas,
            **kwargs,
        )
        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        RedisClusterCache.instance = self
        log.info("redis cluster initalized")

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
                encoder=encoder,
                decoder=decoder,
                namespace=namespace,
                key_prefix=key_prefix,
                key_builder=key_builder,
                **kwargs,
            )
