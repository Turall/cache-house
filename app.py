from cache_house.backends.redis_backend import RedisCache
from cache_house.cache import cache
from time import sleep
import asyncio

RedisCache.init()

@cache(expire=30, namespace="test", key_prefix="tural")
async def test_print(a,b):
    print("OKKKKK")
    # sleep(3)
    return [a,b]


if __name__ == "__main__":
    # for i in range(20):
    #     print(test_print(i, i+1))
    # RedisCache.instance.clear_keys("fastcache:main")

    print(asyncio.run(test_print(1,2)))