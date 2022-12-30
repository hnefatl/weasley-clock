import pathlib
import pydantic

from typing import Mapping, Optional, Union, DefaultDict


class HashableBaseModel(pydantic.BaseModel):
    def __hash__(self):
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


Sources = dict[HAInstance, frozenset[Person]]


def load_config(path: Optional[pathlib.Path] = None) -> Sources:
    if path is None:
        path = pathlib.Path("people.json")

    sources: DefaultDict[HAInstance, Person] = DefaultDict(set)
    for config_entry in pydantic.parse_file_as(list[_ConfigEntry], path):
        sources[config_entry].update(config_entry.people)
    return sources
