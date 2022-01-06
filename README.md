
<div align="center"> <h2> Caching tool for python, working with Redis single instance and Redis cluster mode <h1> </div>


[PyPi link](https://pypi.org/project/cache-house/)

### Installation ###

```sh
 $ pip install cache-house 
```
or with poetry
```sh
poetry add cache-house
```


*****
### ***Quick Start*** ###
*****

cache decorator work with async and sync functions

```python
from cache_house.backends.redis_backend import RedisCache
from cache_house.cache import cache
import asyncio

RedisCache.init()

@cache() # default expire time is 180 seconds
async def test_cache(a: int,b: int):
    print("async cached")
    return [a,b]

@cache()
def test_cache_1(a: int, b: int):
    print("cached")
    return [a, b]


if __name__ == "__main__":
    print(test_cache_1(3,4))
    print(asyncio.run(test_cache(1,2)))
```

Check stored cache key
```sh
➜ $ rdcli KEYS "*"
1) cachehouse:main:8f65aed1010f0062a783c83eb430aca0
2) cachehouse:main:f665833ea64e4fc32653df794257ca06

```

*****
### ***Setup Redis cache instance***
*****

You can pass all [redis-py](https://github.com/redis/redis-py) arguments to  RedisCache.init method and additional arguments : 

```python
def RedisCache.init(
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = ...,
        decoder: Callable[..., Any] = ...,
        namespace: str = ...,
        key_prefix: str = ...,
        key_builder: Callable[..., Any] = ...,
        password: str = ...,
        db: int = ...,
        **kwargs
    )
```
or you can set your own encoder and decoder functions

```python
from cache_house.backends.redis_backend import RedisCache

def custom_encoder(data):
    return json.dumps(data)

def custom_decoder(data):
    return json.loads(data)

RedisCache.init(encoder=custom_encoder, decoder=custom_decoder)

```

#### ***Default encoder and decoder is pickle module.***

*****
### ***Setup Redis Cluster cache instance***
*****

All manipulation with RedisCache  same with a RedisClusterCache

```python

from cache_house.backends.redis_cluster_backend import RedisClusterCache
from cache_house.cache import cache

RedisClusterCache.init()

@cache()
async def test_cache(a: int,b: int):
    print("cached")
    return [a,b]

```

```python 

def RedisClusterCache.init(
        cls,
        host="localhost",
        port=6379,
        encoder: Callable[..., Any] = pickle_encoder,
        decoder: Callable[..., Any] = pickle_decoder,
        startup_nodes=None,
        cluster_error_retry_attempts: int = 3,
        require_full_coverage: bool = True,
        skip_full_coverage_check: bool = False,
        reinitialize_steps: int = 10,
        read_from_replicas: bool = False,
        namespace: str = DEFAULT_NAMESPACE,
        key_prefix: str = DEFAULT_PREFIX,
        key_builder: Callable[..., Any] = key_builder,
        **kwargs,
    )
```

*****
### ***Setup cache instance with FastAPI***
*****


```python

import logging
import uvicorn
from fastapi.applications import FastAPI
from cache_house.backends.redis_backend import RedisCache
from cache_house.cache import cache

app = FastAPI()


@app.on_event("startup")
async def startup():
    print("app started")
    RedisCache.init()


@app.on_event("shutdown")
async def shutdown():
    print("SHUTDOWN")
    RedisCache.close_connections()

@app.get("/notcached")
async def test_route():
    print("notcached")
    return {"hello": "world"}


@app.get("/cached")
@cache()
async def test_route():
    print("cached") # second time when you request this print is not working
    return {"hello": "world"}

if __name__ == "__main__":
    uvicorn.run(app, port=8033)

```


*****
### You can set expire time (seconds) , namespace and key prefix in cache decorator ###
*****

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

*****
### ***If your function works with non-standard data types, you can pass custom encoder and decoder functions to the *cache* decorator.***
*****

```python

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

```

Check stored cache
```sh
rdcli KEYS "*"
1) cachehouse:main:8f65aed1010f0062a783c83eb430aca0
2) cachehouse:custom:f665833ea64e4fc32653df794257ca06
```
*****
### ***All examples works fine with Redis Cluster and single Redis instance.***
*****

# Contributing #

#### Free to open issue and send PR ####

### cache-house  supports Python >= 3.7
