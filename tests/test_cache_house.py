import asyncio
import json
from unittest.mock import patch

import pytest
from fakeredis import FakeAsyncRedis, FakeRedis

from cache_house import __version__
from cache_house.backends import RedisFactory
from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache
from cache_house.cache import cache
from cache_house.helpers import (
    DEFAULT_NAMESPACE,
    DEFAULT_PREFIX,
    key_builder,
    pickle_decoder,
    pickle_encoder,
)


def custom_encoder():
    pass


def custom_decoder():
    pass


def custom_key_builder():
    pass


def _reset_backends():
    RedisCache.instance = None
    RedisClusterCache.instance = None
    RedisFactory.instance = None


def test_version():
    assert __version__ == "1.1.0"


@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_redis_init_defaults():
    _reset_backends()
    RedisCache.init()
    assert RedisCache.instance is not None
    assert RedisCache.instance.encoder == pickle_encoder
    assert RedisCache.instance.decoder == pickle_decoder
    assert RedisCache.instance.key_builder == key_builder
    assert RedisCache.instance.key_prefix == DEFAULT_PREFIX
    assert RedisCache.instance.namespace == DEFAULT_NAMESPACE
    assert RedisCache.instance._async_client_args is not None
    _reset_backends()


@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_redis_init_with_args():
    _reset_backends()
    RedisCache.init(
        host="localhost",
        port=6378,
        db=1,
        encoder=custom_encoder,
        decoder=custom_decoder,
        namespace="test",
        key_prefix="pytest",
        key_builder=custom_key_builder
    )

    assert RedisCache.instance.encoder == custom_encoder
    assert RedisCache.instance.decoder == custom_decoder
    assert RedisCache.instance.key_builder == custom_key_builder
    assert RedisCache.instance.key_prefix == "pytest"
    assert RedisCache.instance.namespace == "test"
    _reset_backends()


@patch("cache_house.backends.redis_cluster_backend.AsyncRedisCluster", FakeAsyncRedis)
@patch("cache_house.backends.redis_cluster_backend.RedisCluster", FakeRedis)
def test_redis_cluster_init_defaults():
    _reset_backends()
    RedisClusterCache.init()
    assert RedisClusterCache.instance is not None
    assert RedisClusterCache.instance.encoder == pickle_encoder
    assert RedisClusterCache.instance.decoder == pickle_decoder
    assert RedisClusterCache.instance.key_builder == key_builder
    assert RedisClusterCache.instance.key_prefix == DEFAULT_PREFIX
    assert RedisClusterCache.instance.namespace == DEFAULT_NAMESPACE
    assert RedisClusterCache.instance._async_client_args is not None
    _reset_backends()


@patch("cache_house.backends.redis_cluster_backend.AsyncRedisCluster", FakeAsyncRedis)
@patch("cache_house.backends.redis_cluster_backend.RedisCluster", FakeRedis)
def test_redis_cluster_init_with_args():
    _reset_backends()
    RedisClusterCache.init(
        host="localhost",
        port=6378,
        encoder=custom_encoder,
        decoder=custom_decoder,
        namespace="test",
        key_prefix="pytest",
        key_builder=custom_key_builder
    )

    assert RedisClusterCache.instance.encoder == custom_encoder
    assert RedisClusterCache.instance.decoder == custom_decoder
    assert RedisClusterCache.instance.key_builder == custom_key_builder
    assert RedisClusterCache.instance.key_prefix == "pytest"
    assert RedisClusterCache.instance.namespace == "test"
    _reset_backends()


@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_sync_cache_roundtrip_single_encode():
    _reset_backends()
    RedisFactory.init(autodetect_cluster=False, namespace="sync_roundtrip")

    calls = {"count": 0}

    @cache(expire=60)
    def sync_roundtrip(x: int):
        calls["count"] += 1
        return {"value": x}

    assert sync_roundtrip(1) == {"value": 1}
    assert sync_roundtrip(1) == {"value": 1}
    assert calls["count"] == 1
    _reset_backends()


@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_sync_cache_preserves_falsy_values():
    _reset_backends()
    RedisFactory.init(autodetect_cluster=False, namespace="sync_falsy")

    calls = {"count": 0}

    @cache(expire=60)
    def sync_falsy():
        calls["count"] += 1
        return 0

    assert sync_falsy() == 0
    assert sync_falsy() == 0
    assert calls["count"] == 1
    _reset_backends()


@pytest.mark.asyncio
@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
async def test_async_cache_roundtrip_awaits_redis():
    _reset_backends()
    RedisFactory.init(autodetect_cluster=False, namespace="async_roundtrip")

    calls = {"count": 0}

    @cache(expire=60)
    async def async_roundtrip(x: int):
        calls["count"] += 1
        return {"value": x}

    assert await async_roundtrip(1) == {"value": 1}
    assert await async_roundtrip(1) == {"value": 1}
    assert calls["count"] == 1
    await RedisFactory.aclose_connections()
    _reset_backends()


@pytest.mark.asyncio
@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
async def test_async_cache_custom_encoder():
    _reset_backends()
    RedisFactory.init(autodetect_cluster=False, namespace="async_json")

    calls = {"count": 0}

    @cache(
        expire=60,
        encoder=lambda data: json.dumps(data).encode(),
        decoder=lambda data: json.loads(data.decode()),
    )
    async def async_json(x: int):
        calls["count"] += 1
        return {"value": x}

    assert await async_json(2) == {"value": 2}
    assert await async_json(2) == {"value": 2}
    assert calls["count"] == 1
    await RedisFactory.aclose_connections()
    _reset_backends()


@patch("cache_house.backends.redis_backend.aioredis.Redis", FakeAsyncRedis)
@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_async_cache_survives_multiple_asyncio_run():
    """asyncio.run() closes its loop; async Redis must rebind on the next run."""
    _reset_backends()
    RedisFactory.init(autodetect_cluster=False, namespace="async_multi_loop")

    calls = {"count": 0}

    @cache(expire=60)
    async def async_multi_loop(x: int):
        calls["count"] += 1
        return {"value": x}

    assert asyncio.run(async_multi_loop(1)) == {"value": 1}
    assert asyncio.run(async_multi_loop(1)) == {"value": 1}
    assert calls["count"] == 1
    _reset_backends()
