from collections import defaultdict
import dataclasses
import pathlib
import pydantic

from typing import Optional, TypeVar, ParamSpec


T = TypeVar("T")
P = ParamSpec("P")

Location = str


class HashableBaseModel(pydantic.BaseModel):
    def __hash__(self) -> int:  # pyright: ignore[reportIncompatibleVariableOverride]
        return hash((type(self),) + tuple(self.__dict__.values()))


class ConfigHAInstance(HashableBaseModel):
    url: str
    token: str


class ConfigPerson(HashableBaseModel):
    name: str
    id: str


class _ConfigEntry(ConfigHAInstance):
    """Used purely for JSON structure, these are converted into dict keys."""

    people: frozenset[ConfigPerson]


@dataclasses.dataclass
class Config:
    sources: dict[ConfigHAInstance, set[ConfigPerson]]


def load_config(path: Optional[pathlib.Path] = None) -> Config:
    if path is None:
        path = pathlib.Path("people.json")

    sources = defaultdict[ConfigHAInstance, set[ConfigPerson]](set)
    for config_entry in pydantic.parse_file_as(list[_ConfigEntry], path):
        sources[config_entry].update(config_entry.people)
    return Config(sources=sources)
