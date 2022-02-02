import logging
from typing import Callable, Any, Union
from datetime import timedelta

from redis import Redis
from cache_house.helpers import (
    pickle_encoder,
    pickle_decoder,
    DEFAULT_PREFIX,
    DEFAULT_NAMESPACE,
    key_builder,
)


log = logging.getLogger(__name__)


class RedisCache:
    instance = None

    def __init__(
        self,
        password: str = None,
        db: int = 0,
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        **kwargs,
    ) -> None:
        self.redis = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            **kwargs,
        )
        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        RedisCache.instance = self
        log.info("redis intialized")
        log.info(f"send ping to redis {self.redis.ping()}")

    def set_key(self, key, val, exp: Union[timedelta, int]):
        val = self.encoder(val)
        self.redis.set(key, val, ex=exp)

    def get_key(self, key: str):
        val = self.redis.get(key)
        if val:
            val = self.decoder(val)
        return val

    @classmethod
    def get_instance(cls):
        if cls.instance:
            return cls.instance
        raise Exception("You mus be initialize redis first")

    @classmethod
    def clear_keys(cls, pattern: str):
        ns_keys = pattern + "*"
        for key in cls.instance.redis.scan_iter(match=ns_keys):
            print(key)
            if key:
                print("find")
                cls.instance.redis.delete(key)
        return True

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
                **kwargs,
            )
