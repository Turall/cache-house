import hashlib
import pickle
from datetime import timedelta
from typing import Any, Tuple

DEFAULT_EXPIRE_TIME = timedelta(seconds=180)
DEFAULT_NAMESPACE = "main"
DEFAULT_PREFIX = "cachehouse"


def _normalize_args(args: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """
    Normalize arguments for key building.

    - For bound methods, replace the first argument (`self`) with the class name.
      This makes caching work for class methods like `Operation().cached_hello()`,
      where each call creates a new instance, but you still want the same cache key.
    """
    if not args:
        return args

    first = args[0]

    # Treat non-primitive objects as potential `self` and replace with class name
    primitive_types = (str, bytes, int, float, bool)
    if not isinstance(first, primitive_types):
        try:
            cls_name = first.__class__.__name__
            return (cls_name, *args[1:])
        except Exception:
            # Fallback: keep original args if anything goes wrong
            return args

    return args


def key_builder(
    module: str,
    name: str,
    args,
    kwargs,
    prefix: str = DEFAULT_PREFIX,
    namespace: str = DEFAULT_NAMESPACE,
):
    """Build key for caching data.

    The default implementation:
    - Uses a stable prefix/namespace
    - Normalizes method calls so `self` does not break caching
    - Hashes module, function name, args, and kwargs
    """

    prefix = f"{prefix}:{namespace}:"

    normalized_args = _normalize_args(tuple(args))
    raw_key = f"{module}:{name}:{normalized_args}:{kwargs}"

    return f"{prefix}:{hashlib.md5(raw_key.encode()).hexdigest()}"


def pickle_encoder(data):
    return pickle.dumps(data)


def pickle_decoder(data):
    return pickle.loads(data)
