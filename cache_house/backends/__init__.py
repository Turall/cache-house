from __future__ import annotations

import contextlib
import logging
from typing import Any, Callable

from redis import Redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache
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

    @staticmethod
    def _is_cluster_enabled(
        host: str,
        port: int,
        password: str | None = None,
        db: int = 0,
        **redis_kwargs: Any,
    ) -> bool:
        """
        Detect whether the target Redis node is part of a Redis Cluster.

        It sends `CLUSTER INFO` command to the node. Standalone Redis will
        respond with an error, while cluster nodes will return cluster info.
        """
        client: Redis | None = None
        try:
            client = Redis(host=host, port=port, password=password, db=db, **redis_kwargs)
            # If this command succeeds, we are talking to a cluster node.
            client.execute_command("CLUSTER INFO")
            log.info("Redis cluster mode detected via CLUSTER INFO")
            return True
        except (ConnectionError, TimeoutError) as e:
            log.warning(f"Could not connect to Redis for cluster detection: {e}. Assuming standalone mode.")
            return False
        except RedisError:
            # Connected to Redis but CLUSTER INFO failed - it's standalone
            log.info("Redis standalone mode detected")
            return False
        except Exception as exc:  # pragma: no cover - defensive
            log.warning(f"Failed to auto-detect Redis cluster mode: {exc}")
            return False
        finally:
            if client is not None:
                with contextlib.suppress(Exception):
                    client.close()

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
        autodetect_cluster: bool = True,
        fallback_to_memory: bool = True,
        **redis_kwargs,
    ):
        """
        Initialize Redis cache backend.

        - If `cluster_mode` is True, always use `RedisClusterCache`.
        - If `cluster_mode` is False and `autodetect_cluster` is True (default),
          it will auto-detect whether the target is a Redis Cluster node by
          issuing `CLUSTER INFO` command and choose the appropriate backend.
        - If `autodetect_cluster` is False, always use standalone `RedisCache`.
        """
        if not cls.instance:
            try:
                use_cluster = cluster_mode
                if not cluster_mode and autodetect_cluster:
                    if cls._is_cluster_enabled(
                        host=host,
                        port=port,
                        password=password,
                        db=db,
                        **redis_kwargs,
                    ):
                        use_cluster = True
                        log.info(
                            "Auto-detected Redis Cluster; using RedisClusterCache backend"
                        )

                if use_cluster:
                    backend = RedisClusterCache(
                        host=host,
                        port=port,
                        encoder=encoder,
                        decoder=decoder,
                        namespace=namespace,
                        key_prefix=key_prefix,
                        key_builder=key_builder,
                        fallback_to_memory=fallback_to_memory,
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
                        fallback_to_memory=fallback_to_memory,
                        **redis_kwargs,
                    )

                cls.instance = backend.instance
            except Exception as err:
                # Handle any unexpected errors during initialization
                log.error(f"Failed to initialize Redis cache: {err}")
                log.warning("Cache operations will be skipped until Redis is available.")

    @classmethod
    def get_instance(cls):
        if cls.instance:
            return cls.instance
        log.warning("Redis is not initialized. Cache operations will be skipped.")
        return None

    @classmethod
    def close_connections(cls):
        if cls.instance:
            try:
                cls.instance.redis.close()
                log.info("close redis connection")
            except Exception as e:
                log.warning(f"Error closing Redis connection: {e}")


__all__ = [
    "RedisCache",
    "RedisClusterCache",
    "DEFAULT_NAMESPACE",
    "DEFAULT_PREFIX",
    "key_builder",
    "pickle_decoder",
    "pickle_encoder",
]
