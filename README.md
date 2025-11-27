
<div align="center"> <h2> Caching tool for python, working with Redis single instance and Redis cluster mode <h1> </div>


[PyPi link](https://pypi.org/project/cache-house/)

### Features ###

- ✅ **Automatic reconnection**: Redis client handles reconnection automatically
- ✅ **Graceful degradation**: Falls back to in-memory cache when Redis is unavailable
- ✅ **No crashes**: All operations handle errors gracefully
- ✅ **Async & Sync support**: Works with both async and sync functions
- ✅ **Redis Cluster support**: Works with single Redis instance and Redis Cluster
- ✅ **Custom encoders/decoders**: Support for custom serialization

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

Cache decorator works with both async and sync functions. The library automatically handles Redis reconnection and falls back to in-memory cache when Redis is unavailable.

```python
from cache_house.backends import RedisFactory
from cache_house.cache import cache
import asyncio

# Initialize Redis with fallback enabled (recommended for production)
RedisFactory.init(fallback_to_memory=True)

@cache()  # default expire time is 180 seconds
async def test_cache(a: int, b: int):
    print("async cached - this only prints on cache miss")
    return [a, b]

@cache()
def test_cache_1(a: int, b: int):
    print("cached - this only prints on cache miss")
    return [a, b]


if __name__ == "__main__":
    print("First call (cache miss):")
    print(test_cache_1(3, 4))
    print("\nSecond call (cache hit):")
    print(test_cache_1(3, 4))  # This will use cache, print won't execute
    
    print("\nAsync function:")
    print(asyncio.run(test_cache(1, 2)))
    print(asyncio.run(test_cache(1, 2)))  # Cached
```

**Output:**
```
First call (cache miss):
cached - this only prints on cache miss
[3, 4]

Second call (cache hit):
[3, 4]  # No print - served from cache

Async function:
async cached - this only prints on cache miss
[1, 2]
[1, 2]  # Cached
```

Check stored cache keys:
```sh
➜ $ rdcli KEYS "*"
1) cachehouse:main:8f65aed1010f0062a783c83eb430aca0
2) cachehouse:main:f665833ea64e4fc32653df794257ca06
```

*****
### ***Setup Redis cache instance***
*****

You can pass all [redis-py](https://github.com/redis/redis-py) arguments to `RedisFactory.init` method and additional arguments: 

```python
def RedisFactory.init(
        host: str = "localhost",
        port: int = 6379,
        encoder: Callable[..., Any] = ...,
        decoder: Callable[..., Any] = ...,
        namespace: str = ...,
        key_prefix: str = ...,
        key_builder: Callable[..., Any] = ...,
        password: str = ...,
        db: int = ...,
        cluster_mode: bool = False,        # Force cluster mode (skip auto-detection)
        autodetect_cluster: bool = True,   # Auto-detect if Redis is running in cluster mode
        fallback_to_memory: bool = True,   # Enable in-memory fallback when Redis is unavailable
        **redis_kwargs
    )
```

#### ***Cluster auto-detection***

By default (`autodetect_cluster=True`), `RedisFactory.init` will:

- Try to send `CLUSTER INFO` to the target Redis node
- If the command succeeds → **cluster mode is detected**, and `RedisClusterCache` is used internally
- If the command fails with a Redis error → **standalone mode is assumed**, and `RedisCache` is used

This means you can usually just call:

```python
from cache_house.backends import RedisFactory

RedisFactory.init(
    host="localhost",
    port=6379,
    fallback_to_memory=True,
    # autodetect_cluster=True by default
)
```

and cache-house will automatically choose the correct backend (standalone or cluster) based on the Redis server configuration.

#### ***Explicit modes (optional)***

- **Force standalone Redis (no detection)**:

```python
RedisFactory.init(
    host="localhost",
    port=6379,
    cluster_mode=False,
    autodetect_cluster=False,  # Always use standalone RedisCache
)
```

- **Force Redis Cluster (no detection)**:

```python
RedisFactory.init(
    host="localhost",
    port=6379,
    cluster_mode=True,         # Always use RedisClusterCache
    autodetect_cluster=False,  # Optional, explicit
)
```

#### ***Best Practice: Initialize Redis with fallback enabled***

```python
from cache_house.backends import RedisFactory

# Initialize with fallback to memory cache (default: True)
# Your application will continue working even if Redis is temporarily unavailable
RedisFactory.init(
    host="localhost",
    port=6379,
    password="your_password",  # Optional
    db=0,
    fallback_to_memory=True  # Falls back to in-memory cache when Redis is down
)
```

#### ***Custom encoder and decoder***

```python
from cache_house.backends import RedisFactory
import json

def custom_encoder(data):
    return json.dumps(data)

def custom_decoder(data):
    return json.loads(data)

RedisFactory.init(
    encoder=custom_encoder, 
    decoder=custom_decoder,
    fallback_to_memory=True
)
```

#### ***Default encoder and decoder is pickle module.***

*****
### ***Setup Redis Cluster cache instance***
*****

All manipulation with `RedisCache` is the same with `RedisClusterCache`

```python
from cache_house.backends import RedisFactory
from cache_house.cache import cache

# Initialize Redis Cluster with fallback enabled
RedisFactory.init(
    cluster_mode=True,
    startup_nodes=[
        {"host": "127.0.0.1", "port": "7000"},
        {"host": "127.0.0.1", "port": "7001"},
    ],
    fallback_to_memory=True  # Falls back to in-memory cache when cluster is unavailable
)

@cache()
async def test_cache(a: int, b: int):
    print("cached")
    return [a, b]
```

**Redis Cluster parameters** (all [redis-py cluster](https://redis-py.readthedocs.io/en/stable/cluster.html) arguments are supported):

```python
RedisFactory.init(
    cluster_mode=True,
    startup_nodes=[{"host": "127.0.0.1", "port": "7000"}],
    cluster_error_retry_attempts: int = 3,
    require_full_coverage: bool = True,
    skip_full_coverage_check: bool = False,
    reinitialize_steps: int = 10,
    read_from_replicas: bool = False,
    fallback_to_memory: bool = True,
    **redis_kwargs
)
```

*****
### ***Setup cache instance with FastAPI***
*****

**Best Practice**: Initialize Redis in startup event with fallback enabled. Your application will continue working even if Redis is temporarily unavailable.

```python
import logging
import uvicorn
from fastapi.applications import FastAPI
from cache_house.backends import RedisFactory
from cache_house.cache import cache

app = FastAPI()


@app.on_event("startup")
async def startup():
    # Initialize with fallback - app won't crash if Redis is unavailable
    RedisFactory.init(
        host="localhost",
        port=6379,
        fallback_to_memory=True  # Enable in-memory fallback
    )
    print("App started - Redis cache initialized")


@app.on_event("shutdown")
async def shutdown():
    # Gracefully close connections
    RedisFactory.close_connections()
    print("App shutdown - Redis connections closed")


@app.get("/notcached")
async def test_route():
    print("notcached")
    return {"hello": "world"}


@app.get("/cached")
@cache(expire=60)  # Cache for 60 seconds
async def test_route():
    print("cached")  # This print only runs on cache miss
    return {"hello": "world"}


@app.get("/cached-with-custom-expire")
@cache(expire=300, namespace="api")  # Cache for 5 minutes with custom namespace
async def expensive_operation():
    # Simulate expensive operation
    import time
    time.sleep(1)
    return {"result": "expensive computation"}


if __name__ == "__main__":
    uvicorn.run(app, port=8033)
```


*****
### ***Cache decorator options***
*****

You can set expire time (seconds or timedelta), namespace, and key prefix in the cache decorator:

```python
from datetime import timedelta
from cache_house.cache import cache

# Using seconds
@cache(expire=30, namespace="app", key_prefix="test") 
async def test_cache(a: int, b: int):
    print("cached")
    return [a, b]

# Using timedelta
@cache(expire=timedelta(minutes=5), namespace="app", key_prefix="test")
def test_cache_sync(a: int, b: int):
    print("cached")
    return [a, b]

if __name__ == "__main__":
    print(asyncio.run(test_cache(1, 2)))
    print(test_cache_sync(3, 4))
```

Check stored cache:
```sh
rdcli KEYS "*"
1) test:app:f665833ea64e4fc32653df794257ca06
```

*****
### ***Understanding Namespaces and Key Builders***
*****

#### **Namespaces**

Namespaces help organize your cache keys and make it easier to manage different parts of your application. The default namespace is `"main"`.

**Key Format**: `{prefix}:{namespace}:{hash}`

**Example with different namespaces:**

```python
from cache_house.backends import RedisFactory
from cache_house.cache import cache

RedisFactory.init(fallback_to_memory=True)

# API endpoints namespace
@cache(expire=60, namespace="api")
def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

# Database queries namespace
@cache(expire=300, namespace="database")
def get_user_posts(user_id: int):
    return [{"id": 1, "title": "Post 1"}]

# Configuration namespace
@cache(expire=3600, namespace="config")
def get_app_config():
    return {"setting": "value"}

# Default namespace (if not specified)
@cache(expire=180)
def default_function():
    return "default"
```

**Cache keys will be:**
```
cachehouse:api:abc123...
cachehouse:database:def456...
cachehouse:config:ghi789...
cachehouse:main:jkl012...  # default namespace
```

**Benefits of using namespaces:**
- **Organization**: Group related cache entries together
- **Easy cleanup**: Clear all keys in a specific namespace
- **Multi-tenancy**: Separate cache for different applications/services
- **Debugging**: Easier to identify cache keys in Redis

#### **Global Namespace Configuration**

You can set a default namespace for all cache operations:

```python
from cache_house.backends import RedisFactory

# Set default namespace for all cache operations
RedisFactory.init(
    namespace="myapp",  # All cache keys will use "myapp" namespace by default
    key_prefix="app",  # Change default prefix from "cachehouse" to "app"
    fallback_to_memory=True
)

# This will use "myapp" namespace
@cache(expire=60)
def my_function():
    return "data"

# Override namespace for specific function
@cache(expire=60, namespace="special")
def special_function():
    return "special data"
```

**Resulting keys:**
```
app:myapp:abc123...  # default namespace
app:special:def456...  # overridden namespace
```

#### **Key Prefix**

The key prefix is the first part of every cache key. Default is `"cachehouse"`.

```python
# Global prefix
RedisFactory.init(key_prefix="myapp", namespace="v1")

# Per-decorator prefix (overrides global)
@cache(expire=60, key_prefix="api", namespace="users")
def get_user(id: int):
    return {"id": id}
```

**Key format**: `{key_prefix}:{namespace}:{hash}`

#### **Custom Key Builder**

You can create your own key builder function for complete control over cache key generation:

```python
import hashlib
from cache_house.backends import RedisFactory
from cache_house.cache import cache

def custom_key_builder(module, name, args, kwargs, prefix="cachehouse", namespace="main"):
    """
    Custom key builder function
    
    Args:
        module: Function's module name
        name: Function name
        args: Function positional arguments
        kwargs: Function keyword arguments
        prefix: Key prefix
        namespace: Namespace
    """
    # Example: Create a more readable key
    # Format: prefix:namespace:module.function:arg1:arg2:kwarg1=value1
    key_parts = [prefix, namespace, f"{module}.{name}"]
    
    # Add positional arguments
    for arg in args:
        key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    # Join and create hash for long keys
    key_string = ":".join(key_parts)
    if len(key_string) > 200:  # Redis key length limit
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{namespace}:{key_hash}"
    
    return key_string

# Use custom key builder globally
RedisFactory.init(
    key_builder=custom_key_builder,
    namespace="custom",
    fallback_to_memory=True
)

@cache(expire=60)
def my_function(a: int, b: int, name: str = "test"):
    return {"result": a + b, "name": name}
```

**Or use custom key builder per decorator:**

```python
def simple_key_builder(module, name, args, kwargs, prefix="cache", namespace="app"):
    # Simple key: just use function name and first argument
    first_arg = args[0] if args else "default"
    return f"{prefix}:{namespace}:{name}:{first_arg}"

@cache(expire=60, key_builder=simple_key_builder, namespace="simple")
def get_item(item_id: int):
    return {"id": item_id}
```

**Key builder function signature:**
```python
def key_builder(
    module: str,      # Function's module (e.g., "__main__" or "myapp.services")
    name: str,       # Function name
    args: tuple,     # Positional arguments
    kwargs: dict,     # Keyword arguments
    prefix: str,      # Key prefix
    namespace: str    # Namespace
) -> str:
    # Return the cache key as a string
    return "your:custom:key:format"
```

#### **Clearing Cache by Namespace**

You can clear all cache keys in a specific namespace:

```python
from cache_house.backends import RedisCache

# Clear all keys in a namespace
RedisCache.clear_keys("cachehouse:api")  # Clears all keys starting with "cachehouse:api"

# Or with custom prefix
RedisCache.clear_keys("myapp:database")  # Clears all keys in "database" namespace
```

**Example: Clear cache for a specific namespace**

```python
from cache_house.backends import RedisFactory, RedisCache

RedisFactory.init(namespace="myapp", fallback_to_memory=True)

# Cache some data
@cache(expire=300, namespace="users")
def get_user(id: int):
    return {"id": id}

@cache(expire=300, namespace="posts")
def get_post(id: int):
    return {"id": id}

# Later, clear only "users" namespace
RedisCache.clear_keys("cachehouse:users")  # Only clears users cache
# Posts cache remains intact
```

#### **Best Practices for Namespaces**

1. **Use descriptive namespaces**:
   ```python
   @cache(namespace="api.users")  # Good
   @cache(namespace="x")          # Bad - not descriptive
   ```

2. **Organize by feature or service**:
   ```python
   namespace="api.users"
   namespace="api.products"
   namespace="database.queries"
   namespace="external.api"
   ```

3. **Use consistent naming**:
   ```python
   # Good - consistent pattern
   namespace="v1.api"
   namespace="v1.database"
   namespace="v2.api"
   ```

4. **Set global namespace for multi-tenant apps**:
   ```python
   # Different namespace per tenant
   tenant_id = get_current_tenant()
   RedisFactory.init(namespace=f"tenant_{tenant_id}")
   ```

5. **Use namespaces for cache invalidation**:
   ```python
   # When user data changes, clear user namespace
   def update_user(user_id):
       # ... update logic ...
       RedisCache.clear_keys("cachehouse:users")  # Clear all user cache
   ```

*****
### ***Custom encoder and decoder in decorator***
*****

If your function works with non-standard data types, you can pass custom encoder and decoder functions to the cache decorator:

```python
import asyncio
import json
from cache_house.backends import RedisFactory
from cache_house.cache import cache

RedisFactory.init(fallback_to_memory=True)

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

Check stored cache:
```sh
rdcli KEYS "*"
1) cachehouse:main:8f65aed1010f0062a783c83eb430aca0
2) cachehouse:custom:f665833ea64e4fc32653df794257ca06
```

*****
### ***Error Handling and Resilience***
*****

**cache-house** is designed to be resilient and won't crash your application:

#### **Automatic Reconnection**
Redis client handles reconnection automatically. You don't need to manage connections manually.

#### **In-Memory Fallback**
When Redis is unavailable, cache operations automatically fall back to in-memory cache:

```python
from cache_house.backends import RedisFactory
from cache_house.cache import cache

# Initialize with fallback enabled (default: True)
RedisFactory.init(
    host="localhost",
    port=6379,
    fallback_to_memory=True  # Falls back to in-memory cache when Redis is down
)

@cache(expire=60)
def expensive_operation(data):
    # This function will work even if Redis is unavailable
    # Results will be cached in memory temporarily
    return process_data(data)
```

#### **Graceful Error Handling**
All cache operations handle errors gracefully:

```python
from cache_house.backends import RedisFactory
from cache_house.cache import cache

# Even if Redis is not initialized, your code won't crash
cache_instance = RedisFactory.get_instance()
if cache_instance is None:
    print("Cache not available, but app continues running")

@cache(expire=60)
def my_function():
    # If Redis fails, this function still executes normally
    # Cache errors are logged but don't crash the app
    return expensive_computation()
```

#### **Best Practices**

1. **Always enable fallback for production**:
   ```python
   RedisFactory.init(fallback_to_memory=True)
   ```

2. **Handle cache as optional**:
   ```python
   @cache(expire=60)
   def my_function():
       # Function works with or without cache
       return compute_result()
   ```

3. **Use appropriate expiration times**:
   ```python
   @cache(expire=300)  # 5 minutes for stable data
   def get_stable_data():
       return fetch_data()
   
   @cache(expire=30)  # 30 seconds for frequently changing data
   def get_dynamic_data():
       return fetch_data()
   ```

4. **Close connections on shutdown** (e.g., in FastAPI):
   ```python
   @app.on_event("shutdown")
   async def shutdown():
       RedisFactory.close_connections()
   ```

*****
### ***Complete Example: Production-Ready Setup***
*****

Here's a complete example showing best practices for using cache-house in production:

```python
import asyncio
import logging
from datetime import timedelta
from cache_house.backends import RedisFactory
from cache_house.cache import cache

# Configure logging to see cache operations
logging.basicConfig(level=logging.INFO)

# Initialize Redis with fallback enabled
# Your app will work even if Redis is temporarily unavailable
RedisFactory.init(
    host="localhost",
    port=6379,
    password=None,  # Set if your Redis requires authentication
    db=0,
    fallback_to_memory=True,  # Enable in-memory fallback
    # You can pass any redis-py connection arguments here
    socket_connect_timeout=5,
    socket_timeout=5,
)

# Example 1: Cache expensive computation
@cache(expire=300)  # Cache for 5 minutes
def expensive_computation(n: int):
    """This expensive operation will be cached"""
    result = sum(i * i for i in range(n))
    print(f"Computed result for {n}: {result}")
    return result

# Example 2: Cache API response
@cache(expire=60, namespace="api")  # Cache for 1 minute with namespace
async def fetch_user_data(user_id: int):
    """Simulate API call - will be cached"""
    print(f"Fetching user {user_id} from API...")
    await asyncio.sleep(0.1)  # Simulate network delay
    return {"user_id": user_id, "name": f"User {user_id}"}

# Example 3: Cache with custom expiration
@cache(expire=timedelta(hours=1), namespace="long_term")
def get_configuration():
    """Configuration that changes rarely"""
    print("Loading configuration...")
    return {"setting1": "value1", "setting2": "value2"}

# Example 4: Cache database query result
@cache(expire=180, namespace="database")
async def get_user_posts(user_id: int):
    """Simulate database query"""
    print(f"Querying database for user {user_id} posts...")
    await asyncio.sleep(0.05)
    return [{"id": 1, "title": "Post 1"}, {"id": 2, "title": "Post 2"}]

async def main():
    print("=== Example 1: Expensive computation ===")
    print(expensive_computation(1000000))  # First call - computes
    print(expensive_computation(1000000))  # Second call - from cache
    
    print("\n=== Example 2: API response caching ===")
    print(await fetch_user_data(1))  # First call - fetches
    print(await fetch_user_data(1))  # Second call - from cache
    
    print("\n=== Example 3: Configuration caching ===")
    print(get_configuration())  # First call - loads
    print(get_configuration())  # Second call - from cache
    
    print("\n=== Example 4: Database query caching ===")
    print(await get_user_posts(1))  # First call - queries
    print(await get_user_posts(1))  # Second call - from cache
    
    # Clean up
    RedisFactory.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
```

**Output:**
```
INFO:cache_house.backends.redis_backend:redis initialized (Redis will handle reconnections automatically)
=== Example 1: Expensive computation ===
Computed result for 1000000: 333333333333500000
Computed result for 1000000: 333333333333500000
=== Example 2: API response caching ===
Fetching user 1 from API...
{'user_id': 1, 'name': 'User 1'}
{'user_id': 1, 'name': 'User 1'}
...
```

**Note**: If Redis is unavailable, all operations will still work using the in-memory fallback cache. Your application won't crash!

*****
### ***All examples work with both Redis Cluster and single Redis instance.***
*****

# Contributing #

#### Free to open issue and send PR ####

### cache-house  supports Python >= 3.10
