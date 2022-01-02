import logging
from datetime import timedelta
from typing import Any, Callable, Union

from redis import Redis

from cache_house.backends.base import RedisBaseCache
from cache_house.helpers import (DEFAULT_NAMESPACE, DEFAULT_PREFIX,
                                 key_builder, pickle_decoder, pickle_encoder)

log = logging.getLogger(__name__)


class RedisCache(RedisBaseCache):
    def __init__(self,
                 host: str = "localhost",
                 port: int = 6379,
                 encoder: Callable[..., Any] = ...,
                 decoder: Callable[..., Any] = ...,
                 namespace: str = ...,
                 key_prefix: str = ...,
                 key_builder: Callable[..., Any] = ...,
                 password: str = ...,
                 db: int = ...,
                 **kwargs
                 ) -> None:
        super().__init__(host=host,
                         port=port,
                         encoder=encoder,
                         decoder=decoder,
                         namespace=namespace,
                         key_prefix=key_prefix,
                         key_builder=key_builder,
                         **kwargs
                         )

        if not self.__class__.__name__ == "RedisClusterCache":
            self.password = password
            self.db = db
            self.redis = Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                **kwargs,
            )
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
