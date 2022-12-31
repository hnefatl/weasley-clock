from collections import defaultdict
import pathlib
import pydantic

from typing import Optional


class HashableBaseModel(pydantic.BaseModel):
    def __hash__(self) -> int: # pyright: ignore[reportIncompatibleVariableOverride]
        return hash((type(self),) + tuple(self.__dict__.values()))


class HAInstance(HashableBaseModel):
    url: str
    token: str


class Person(HashableBaseModel):
    name: str
    id: str


class _ConfigEntry(HAInstance):
    """Used purely for JSON structure, these are converted into dict keys."""

    people: frozenset[Person]


Sources = dict[HAInstance, set[Person]]


def load_sources(path: Optional[pathlib.Path] = None) -> Sources:
    if path is None:
        path = pathlib.Path("people.json")

    sources = defaultdict[HAInstance, set[Person]](set)
    for config_entry in pydantic.parse_file_as(list[_ConfigEntry], path):
        sources[config_entry].update(config_entry.people)
    return sources
