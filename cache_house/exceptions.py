class CacheHouseError(Exception):
    """Base exception for all cache-house errors."""


class RedisNotInitialized(CacheHouseError):
    """Raised when Redis backend is used before being initialized."""


# Backwards compatibility alias (older versions exposed this name)
RedisNotInitialize = RedisNotInitialized

