from unittest.mock import patch

from fakeredis import FakeRedis

from cache_house import __version__
from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache
from cache_house.helpers import (DEFAULT_NAMESPACE, DEFAULT_PREFIX,
                                 key_builder, pickle_decoder, pickle_encoder)


def custom_encoder():
    pass


def custom_decoder():
    pass


def custom_key_builder():
    pass


def test_version():
    assert __version__ == "0.1.4"


@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_redis_init_defaults():
    RedisCache.init()
    assert RedisCache.instance is not None
    assert RedisCache.instance.encoder == pickle_encoder
    assert RedisCache.instance.decoder == pickle_decoder
    assert RedisCache.instance.key_builder == key_builder
    assert RedisCache.instance.key_prefix == DEFAULT_PREFIX
    assert RedisCache.instance.namespace == DEFAULT_NAMESPACE
    RedisCache.instance = None


@patch("cache_house.backends.redis_backend.Redis", FakeRedis)
def test_redis_init_with_args():
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
    RedisCache.instance = None


@patch("cache_house.backends.redis_cluster_backend.RedisCluster", FakeRedis)
def test_redis_cluster_init_defaults():
    RedisClusterCache.init()
    print("TTTT" , RedisClusterCache.instance.redis)
    assert RedisClusterCache.instance is not None
    assert RedisClusterCache.instance.encoder == pickle_encoder
    assert RedisClusterCache.instance.decoder == pickle_decoder
    assert RedisClusterCache.instance.key_builder == key_builder
    assert RedisClusterCache.instance.key_prefix == DEFAULT_PREFIX
    assert RedisClusterCache.instance.namespace == DEFAULT_NAMESPACE
    RedisClusterCache.instance = None


@patch("cache_house.backends.redis_cluster_backend.RedisCluster", FakeRedis)
def test_redis_cluster_init_with_args():
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
    RedisClusterCache.instance = None
