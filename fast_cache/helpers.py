from typing import Callable, Any
from functools import wraps
import hashlib

def cache(f: Callable[..., Any]):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = key_builder(f.__module__, f.__name__, args, kwargs)
        print(key)

    return wrapper


def key_builder(module: str, name:str ,args, kwargs,prefix:str = "fastcache", namespace: str = "main"):
    prefix = f"{prefix}:{namespace}:"
    cache_key = (
        prefix
        + hashlib.md5(  # nosec:B303
            f"{module}:{name}:{args}:{kwargs}".encode()
        ).hexdigest()
    )
    return cache_key

