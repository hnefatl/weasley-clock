from __future__ import annotations

import dataclasses
import pygame

from typing import Callable, Type, TypeVar, ParamSpec, cast

from homeassistant_api import (
    Client,
    State,
    HomeassistantAPIError,
    ParameterMissingError,
)
from requests.exceptions import RequestException

from config import Config, Location, ConfigPerson, ConfigHAInstance

T = TypeVar("T")
P = ParamSpec("P")

SPECIAL_LOCATIONS = {
    Location("Away"): Location("Elsewhere"),
}


def _wrap_errors(fn: Callable[P, T]) -> Callable[P, T | HomeassistantAPIError]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | HomeassistantAPIError:
        try:
            return fn(*args, **kwargs)
        except HomeassistantAPIError as e:
            return e
        except RequestException as e:
            return HomeassistantAPIError(e)

    return wrapper


def _get_state_attribute(
    state: State, attribute: str, value_type: Type[T]
) -> T | ParameterMissingError:
    value = state.attributes.get(attribute)
    if value is None:
        return ParameterMissingError(
            f"Expected response containing '{attribute}', but got: {state.attributes}"
        )
    return cast(value_type, value)


@dataclasses.dataclass(frozen=True)
class Person:
    name: str
    id: str
    # Just included for hash uniqueness between people on different instances
    instance_url: str
    location: Location
    photo_url: str | HomeassistantAPIError
    photo: pygame.surface.Surface | HomeassistantAPIError = dataclasses.field(
        compare=False
    )

    def update(self, other: Person) -> Person:
        return Person(
            name=self.name,
            id=self.id,
            instance_url=self.instance_url,
            location=self.location,
            photo_url=(
                other.photo_url
                if isinstance(other.photo_url, HomeassistantAPIError)
                else self.photo_url
            ),
            photo=(
                other.photo
                if isinstance(other.photo, HomeassistantAPIError)
                else self.photo
            ),
        )

    def to_config_person(self) -> ConfigPerson:
        return ConfigPerson(name=self.name, id=self.id)


@dataclasses.dataclass
class InstanceSnapshot:
    """A snapshot of state from a single HA instance."""

    people: set[Person]
    locations: set[Location] | HomeassistantAPIError
    errored_people: dict[ConfigPerson, HomeassistantAPIError]


@dataclasses.dataclass
class Snapshot:
    """A snapshot of state from all HA instances."""

    people: set[Person]
    locations: set[Location]
    errored_people: dict[ConfigPerson, HomeassistantAPIError]
    errored_instances: dict[ConfigHAInstance, HomeassistantAPIError]

    @classmethod
    def from_instance_snapshots(
        cls,
        instance_snapshots: dict[
            ConfigHAInstance, InstanceSnapshot | HomeassistantAPIError
        ],
    ) -> Snapshot:
        snapshot = Snapshot(
            people=set(), locations=set(), errored_people={}, errored_instances={}
        )
        for instance, instance_snapshot in instance_snapshots.items():
            if isinstance(instance_snapshot, HomeassistantAPIError):
                snapshot.errored_instances[instance] = instance_snapshot
                continue

            snapshot.people.update(instance_snapshot.people)
            snapshot.errored_people.update(instance_snapshot.errored_people)

            if not isinstance(instance_snapshot.locations, HomeassistantAPIError):
                snapshot.locations.update(instance_snapshot.locations)
            snapshot.locations.update(p.location for p in snapshot.people)

        return snapshot

    def get_error_strings(self) -> list[str]:
        lines: list[str] = []
        for person, error in self.errored_people.items():
            lines.append(f"{person.name}: {error}")
        for instance, error in self.errored_instances.items():
            lines.append(f"{instance.url}: {error}")
        return lines


def fetch_snapshot(config: Config) -> Snapshot:
    @_wrap_errors
    def get_instance_locations(client: Client) -> set[Location]:
        entities = client.get_entities()
        zones = entities.get("zone")
        if zones is None:
            return set()
        return {
            entity.state.attributes.get("friendly_name", id)
            for id, entity in zones.entities.items()
        }

    @_wrap_errors
    def per_instance(
        instance: ConfigHAInstance, people: set[ConfigPerson]
    ) -> InstanceSnapshot:
        with Client(api_url=instance.url, token=instance.token) as client:

            @_wrap_errors
            def get_photo(path: str) -> pygame.surface.Surface:
                raise HomeassistantAPIError("not implemented")
                path = path.removeprefix("/api/")

                data = client.request(  # pyright: ignore[reportUnknownMemberType]
                    path, decode_bytes=False
                )
                # Might need pillow library to load from data...
                return pygame.image.fromstring(data, (512, 512), "RGB")

            @_wrap_errors
            def get_instance_person(config_person: ConfigPerson) -> Person:
                state = client.get_state(entity_id=config_person.id)

                photo_url = _get_state_attribute(state, "entity_picture", str)
                if isinstance(photo_url, HomeassistantAPIError):
                    photo = HomeassistantAPIError(
                        f"Missing photo_url prevents fetching photo: {photo_url}"
                    )
                else:
                    photo = get_photo(photo_url)
                return Person(
                    name=config_person.name,
                    id=config_person.id,
                    instance_url=client.api_url,
                    location=SPECIAL_LOCATIONS.get(state.state, state.state),
                    photo_url=photo_url,
                    photo=photo,
                )

            snapshot = InstanceSnapshot(
                people=set(),
                locations=set(),
                errored_people={},
            )
            for config_person in people:
                result = get_instance_person(config_person)
                if isinstance(result, HomeassistantAPIError):
                    snapshot.errored_people[config_person] = result
                else:
                    snapshot.people.add(result)

                locations = get_instance_locations(client)
                if isinstance(locations, HomeassistantAPIError):
                    snapshot.locations
            return snapshot

    return Snapshot.from_instance_snapshots(
        {
            instance: per_instance(instance, people)
            for instance, people in config.sources.items()
        }
    )
