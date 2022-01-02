import hashlib
import pickle
from datetime import timedelta

DEFAULT_EXPIRE_TIME = timedelta(seconds=180)
DEFAULT_NAMESPACE = "main"
DEFAULT_PREFIX = "cachehouse"


def key_builder(
    module: str,
    name: str,
    args,
    kwargs,
    prefix: str = DEFAULT_PREFIX,
    namespace: str = DEFAULT_NAMESPACE,
):

    """Build key for caching data"""

    prefix = f"{prefix}:{namespace}:"
    cache_key = (
        prefix + hashlib.md5(f"{module}:{name}:{args}:{kwargs}".encode()).hexdigest()
    )
    return cache_key


def pickle_encoder(data):
    return pickle.dumps(data)


def pickle_decoder(data):
    return pickle.loads(data)
