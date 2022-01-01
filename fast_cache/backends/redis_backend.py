import logging
from redis import Redis


log = logging.getLogger(__name__)


class RedisCache:
    instance = None

    def __init__(
        self,
        password: str = None,
        db: int = 0,
        host: str = "localhost",
        port: int = 6379,
        **kwargs,
    ) -> None:
        self.redis = Redis(host=host, port=port, db=db, password=password, **kwargs)
        RedisCache.instance = self
        log.info("redis intialized")
        log.info(f"send ping to redis {self.redis.ping()}")

    def set_key(self, key, val, exp: int):
        self.redis.set(key, val,ex = exp)

    def get_key(self, key: str):
        return self.redis.get(key)

    @classmethod
    def get_instance(cls):
        if cls.instance:
            return cls.instance
        raise Exception("You mus be initialize redis first")

    @classmethod
    def init(
        cls,
        password: str = None,
        db: int = 0,
        host: str = "localhost",
        port: int = 6379,
        **kwargs,
    ):
        if not cls.instance:
            cls(host=host, port=port, db=db, password=password, **kwargs)
