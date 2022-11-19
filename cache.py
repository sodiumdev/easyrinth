import orjson
import typing as tp


class _Cache:
    def __init__(self, data: dict[str, tp.Any]):
        self.value: dict[str, tp.Any] = data

    def __getattr__(self, item: str):
        res: tp.Any = self.value[item]
        if isinstance(res, dict):
            return _Cache(res)

        return res


with open("cache.json", "rb") as config:
    CACHE = _Cache(orjson.loads(config.read()))

__all__ = "__getattr__", "get_cache", "is_cached"


def __getattr__(name: str) -> tp.Any:
    return getattr(CACHE, name)


def is_cached(pid: str):
    return pid in CACHE.value


def cache(pid: str, name: str):
    CACHE.value[pid] = name


def get_cache() -> _Cache:
    return CACHE


def dump():
    with open("cache.json", "wb") as w:
        w.write(orjson.dumps(CACHE.value))
