cache-house is a caching tool for python working with Redis single instance and Redis cluster mode
==============


### Installation ###

```sh
 $ pip install cache-house
```


### Quick Start ###

```python
from cache_house.backends.redis_backend import RedisCache
from cache_house.cache import cache
import asyncio

RedisCache.init()

@cache()
async def test_cache(a: int,b: int):
    print("cached")
    return [a,b]


if __name__ == "__main__":
    print(asyncio.run(test_cache(1,2)))
```

Check stored cache key
```sh
➜ $ rdcli KEYS "*"
1) cachehouse:main:f665833ea64e4fc32653df794257ca06

```

### Setup Redis cache instance

```python
from cache_house.backends.redis_backend import RedisCache

RedisCache.init(host="localhost",port=6379)

```


### You can set expire time (seconds) , namespace and key prefix in cache decorator ###

```python

@cache(expire=30, namespace="app", key_prefix="test")
async def test_cache(a: int,b: int):
    print("cached")
    return [a,b]


if __name__ == "__main__":
    print(asyncio.run(test_cache(1,2)))
```
Check stored cache
```sh
rdcli KEYS "*"
1) test:app:f665833ea64e4fc32653df794257ca06
```





# Contributing #

#### Free to open issue and send PR ####

### cache-house  supports Python >= 3.7
