import logging
from typing import Any, Callable


from redis.cluster import RedisCluster
from redis.exceptions import RedisClusterException
from cache_house.backends.redis_backend import RedisCache
from cache_house.helpers import (
    DEFAULT_NAMESPACE,
    DEFAULT_PREFIX,
    key_builder,
    pickle_decoder,
    pickle_encoder,
)

try:
    from fakeredis import FakeRedis
except ImportError:
    FakeRedis = None

log = logging.getLogger(__name__)


class RedisClusterCache(RedisCache):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = ...,
        decoder: Callable[..., Any] = ...,
        namespace: str = ...,
        key_prefix: str = ...,
        key_builder: Callable[..., Any] = ...,
        startup_nodes: str = None,
        cluster_error_retry_attempts: int = 3,
        require_full_coverage: bool = True,
        skip_full_coverage_check: bool = True,
        reinitialize_steps: int = 10,
        read_from_replicas: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            encoder=encoder,
            decoder=decoder,
            namespace=namespace,
            key_prefix=key_prefix,
            key_builder=key_builder,
            **kwargs,
        )
        try:
            self.redis = RedisCluster(
                self.host,
                self.port,
                startup_nodes,
                cluster_error_retry_attempts,
                require_full_coverage,
                skip_full_coverage_check,
                reinitialize_steps,
                read_from_replicas,
                **kwargs,
            )
            
            if FakeRedis is None:
                log.info(f"redis cluster nodes {self.redis.get_nodes()}")
                log.info("redis cluster initalized")
            RedisClusterCache.instance = self
        except RedisClusterException as err:
            log.error(err)
            log.warning("can not connect to Redis cluster")


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
