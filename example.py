import asyncio
import json
from cache_house.backends.redis_backend import RedisCache
from cache_house.cache import cache

RedisCache.init()

def custom_encoder(data):
    return json.dumps(data)

def custom_decoder(data):
    return json.loads(data)

@cache(expire=30, encoder=custom_encoder, decoder=custom_decoder, namespace="custom")
async def test_cache(a: int, b: int):
    print("async cached")
    return {"a": a, "b": b}


@cache(expire=30)
def test_cache_1(a: int, b: int):
    print("cached")
    return [a, b]


if __name__ == "__main__":
    print(asyncio.run(test_cache(1, 2)))
    print(test_cache_1(3, 4))
