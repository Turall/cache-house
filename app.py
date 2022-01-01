from fast_cache.backends.redis_backend import RedisCache
from fast_cache.cache import cache
from time import sleep
RedisCache.init()

@cache
def test_print():
    print("OKKKKK")
    sleep(3)
    return "ok"


if __name__ == "__main__":
    print(test_print())
