from cache_house.backends.redis_backend import RedisCache
from cache_house.cache import cache
from time import sleep
RedisCache.init(decode_responses=True)

@cache
def test_print(a,b):
    print("OKKKKK")
    # sleep(3)
    return "ok"


if __name__ == "__main__":
    # for i in range(20):
    #     print(test_print(i, i+1))
    RedisCache.instance.clear_keys("fastcache:main")