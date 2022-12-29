from __future__ import annotations

import contextlib
import dataclasses

from typing import Mapping, Optional, Union

from homeassistant_api import Client, State, HomeassistantAPIError

Location = str


@dataclasses.dataclass(frozen=True)
class HAInstance:
    url: str
    token: str


@dataclasses.dataclass(frozen=True)
class HAClient(HAInstance):
    client: Client = dataclasses.field(compare=False)

    @classmethod
    def from_instance(cls, instance: HAInstance, client: Client) -> HAClient:
        return HAClient(url=instance.url, token=instance.token, client=client)


@dataclasses.dataclass(frozen=True)
class Person:
    name: str
    id: str


_KEITH_HA = HAInstance(
    url="https://ha.keith.collister.xyz/api",
    token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiNzA0ZDA2NDM0MDE0MzhlYWFjYTE0NDRlNGYyMTZhMSIsImlhdCI6MTY3MjMyNjE2OSwiZXhwIjoxOTg3Njg2MTY5fQ.xO5X1-JpASvTTr_WBUq0FWzY7FwbcZueW_kvOrAnELg",
)
_PEOPLE = {_KEITH_HA: {Person(name="Keith", id="person.keith")}}


def _get_location_from_person(person: State) -> Location:
    state = person.state
    SPECIAL_LOCATIONS = {
        "Away": "Elsewhere",
    }
    return SPECIAL_LOCATIONS.get(state, state)


def _get_locations(
    sources: Mapping[HAClient, Person]
) -> dict[Person, Union[Location, HomeassistantAPIError]]:
    results = {}
    for client, people in sources.items():
        for person in people:
            try:
                results[person] = _get_location_from_person(
                    client.client.get_state(entity_id=person.id)
                )
            except HomeassistantAPIError as e:
                results[person] = e
    return results


def main():
    with contextlib.ExitStack() as stack:
        _make_client = lambda instance: HAClient.from_instance(
            instance=instance,
            client=stack.enter_context(Client(instance.url, instance.token)),
        )

        sources = {
            _make_client(instance): people for instance, people in _PEOPLE.items()
        }

        try:
            for person, location in _get_locations(sources).items():
                print(f"{person.name}: {location}")
        except HomeassistantAPIError as e:
            print(e)


if __name__ == "__main__":
    main()
