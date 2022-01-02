import logging
from redis.cluster import RedisCluster
from cache_house.backends.redis_backend import RedisCache



log = logging.getLogger(__name__)


class RedisClusterCache(RedisCache):
    instance = None

    def __init__(
        self,
        host=None,
        port=6379,
        startup_nodes=None,
        cluster_error_retry_attempts=3,
        require_full_coverage=True,
        skip_full_coverage_check=False,
        reinitialize_steps=10,
        read_from_replicas=False,
    ) -> None:
        self.redis = RedisCluster(
            host,
            port,
            startup_nodes,
            cluster_error_retry_attempts,
            require_full_coverage,
            skip_full_coverage_check,
            reinitialize_steps,
            read_from_replicas,
        )
        RedisClusterCache.instance = self
        log.info("redis initalized")
        log.info(f"cluster nodes {self.redis.get_nodes()}")

    @classmethod
    def init(
        cls,
        host=None,
        port=6379,
        startup_nodes=None,
        cluster_error_retry_attempts=3,
        require_full_coverage=True,
        skip_full_coverage_check=False,
        reinitialize_steps=10,
        read_from_replicas=False,
    ):
        if not cls.instance:
            cls(
                host,
                port,
                startup_nodes,
                cluster_error_retry_attempts,
                require_full_coverage,
                skip_full_coverage_check,
                reinitialize_steps,
                read_from_replicas,
            )
