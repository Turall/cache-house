from __future__ import annotations
import logging
from typing import Any, Callable

from cache_house.helpers import (DEFAULT_NAMESPACE, DEFAULT_PREFIX,
                                 key_builder, pickle_decoder, pickle_encoder)

log = logging.getLogger(__name__)


class RedisBaseCache:
    instance = None

    def __init__(self,
                 host: str = "localhost",
                 port: int = 6379,
                 encoder: Callable[..., Any] = pickle_encoder,
                 decoder: Callable[..., Any] = pickle_decoder,
                 namespace: str = DEFAULT_NAMESPACE,
                 key_prefix: str = DEFAULT_PREFIX,
                 key_builder: Callable[..., Any] = key_builder,
                 **kwargs
                 ) -> None:
        self.host = host
        self.port = port
        self.encoder = encoder
        self.decoder = decoder
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.key_builder = key_builder
        self.kwargs = kwargs

    @classmethod
    def get_instance(cls):
        if cls.instance:
            return cls.instance
        log.error("Redis is not intialized")
