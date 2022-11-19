import orjson
import typing as tp


class _Config:
    def __init__(self, config: tp.Mapping[str, tp.Any]):
        self.value: tp.Mapping[str, tp.Any] = config

    def __getattr__(self, item: str):
        res: tp.Any = self.value[item]
        if isinstance(res, tp.Mapping):
            return _Config(res)

        return res


with open("config.json", "r") as config:
    CONFIG = _Config(orjson.loads(config.read()))

__all__ = "__getattr__", "get_config"


def __getattr__(name: str) -> tp.Any:
    return getattr(CONFIG, name)


def get_config() -> _Config:
    return CONFIG
