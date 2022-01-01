import hashlib


def key_builder(
    module: str,
    name: str,
    args,
    kwargs,
    prefix: str = "fastcache",
    namespace: str = "main",
):
    prefix = f"{prefix}:{namespace}:"
    cache_key = (
        prefix + hashlib.md5(f"{module}:{name}:{args}:{kwargs}".encode()).hexdigest()
    )
    return cache_key
