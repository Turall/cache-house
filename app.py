from cache_house.backends.redis_backend import RedisCache
from cache_house.backends.redis_cluster_backend import RedisClusterCache
from cache_house.cache import cache
from time import sleep
import asyncio

RedisClusterCache.init()

@cache(expire=30, namespace="app", key_prefix="test")
async def test_cache(a: int,b: int):
    print("async cached")
    return [a,b]


@cache(expire=30,  key_prefix="test")
def test_cache_1(a: int,b: int):
    print("cached")
    return [a,b]

if __name__ == "__main__":
    # for i in range(20):
    #     print(test_print(i, i+1))
    # RedisCache.instance.clear_keys("fastcache:main")

    print(asyncio.run(test_cache(1,2)))
    print(test_cache_1(3,4))