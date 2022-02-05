from __future__ import annotations
import logging
from typing import Any, Callable
from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache
from redis.connection import parse_url

from cache_house.helpers import (
    DEFAULT_NAMESPACE,
    DEFAULT_PREFIX,
    key_builder,
    pickle_decoder,
    pickle_encoder,
)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RedisFactory:
    instance = None

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        **redis_kwargs,
    ) -> None:
        self.host = host
        self.port = port
        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        self.redis_kwargs = redis_kwargs

    @classmethod
    def init(
        cls,
        password: str = None,
        db: int = 0,
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        cluster_mode: bool = False,
        **redis_kwargs,
    ):
        # print(parse_url(host))
        if not cls.instance:
            backend = None
            try:
                if cluster_mode:
                    backend = RedisClusterCache(
                        host=host,
                        port=port,
                        encoder=encoder,
                        decoder=decoder,
                        namespace=namespace,
                        key_prefix=key_prefix,
                        key_builder=key_builder,
                        url=None,
                        **redis_kwargs,
                    )
                else:
                    backend = RedisCache(
                        host=host,
                        port=port,
                        db=db,
                        password=password,
                        encoder=encoder,
                        decoder=decoder,
                        namespace=namespace,
                        key_prefix=key_prefix,
                        key_builder=key_builder,
                        **redis_kwargs,
                    )
                cls.instance = backend.instance
            except Exception as err:
                log.error(err)


    @classmethod
    def get_instance(cls):
        if cls.instance:
            return cls.instance
        log.error("Redis is not intialized")

    @classmethod
    def close_connections(cls):
        if cls.instance:
            cls.instance.redis.close()
            log.info("close redis connection")


__all__ = [
    "RedisCache",
    "RedisClusterCache",
    "DEFAULT_NAMESPACE",
    "DEFAULT_PREFIX",
    "key_builder",
    "pickle_decoder",
    "pickle_encoder",
]
