import dataclasses

from homeassistant_api import Client, State, HomeassistantAPIError, processing

from typing import TypeVar, Callable, cast

from config import *

T = TypeVar("T")
Location = str


@processing.Processing.processor("image/jpeg")  # type: ignore[arg-type]
def process_jpeg(response: processing.ResponseType) -> bytes:
    """Returns the plaintext of the reponse."""
    return response.content


def _with_client(
    instance: HAInstance, fn: Callable[[Client], T]
) -> T | HomeassistantAPIError:
    try:
        with Client(api_url=instance.url, token=instance.token) as client:
            return fn(client)
    except HomeassistantAPIError as e:
        return e


@dataclasses.dataclass(frozen=True)
class PersonState:
    person: Person
    instance: HAInstance
    state: State = dataclasses.field(compare=False)

    def get_location(self) -> Location:
        state = self.state.state
        SPECIAL_LOCATIONS = {
            "Away": "Elsewhere",
        }
        return SPECIAL_LOCATIONS.get(state, state)

    def get_image_path(self) -> Optional[str]:
        return self.state.attributes.get("entity_picture")

    def get_image(self) -> Optional[bytes] | HomeassistantAPIError:
        path = self.get_image_path()
        if path is None:
            return None
        path = path.removeprefix("/api/")

        data = _with_client(
            self.instance,
            lambda client: client.request(  # pyright: ignore[reportUnknownMemberType]
                path, decode_bytes=False
            ),
        )
        return cast(bytes, data)


def get_person_state_from_client(
    client: Client, person: Person
) -> PersonState | HomeassistantAPIError:
    try:
        return PersonState(
            person=person,
            instance=HAInstance(url=client.api_url, token=client.token),
            state=client.get_state(entity_id=person.id),
        )
    except HomeassistantAPIError as e:
        return e


def get_person_state(
    instance: HAInstance, person: Person
) -> PersonState | HomeassistantAPIError:
    return _with_client(
        instance, lambda client: get_person_state_from_client(client, person)
    )


def get_person_states(
    sources: Sources,
) -> tuple[set[PersonState], dict[Person, HomeassistantAPIError]]:
    successes = set[PersonState]()
    failures = dict[Person, HomeassistantAPIError]()
    for instance, people in sources.items():
        try:
            with Client(api_url=instance.url, token=instance.token) as client:
                for person in people:
                    try:
                        result = get_person_state_from_client(client, person)
                        if isinstance(result, HomeassistantAPIError):
                            failures[person] = result
                        else:
                            successes.add(result)
                    except HomeassistantAPIError as e:
                        failures[person] = e
        except HomeassistantAPIError as e:
            # If the client itself fails creation, then mark all associated people as errored.
            failures.update({person: e for person in people})

    return (successes, failures)


def get_all_locations(instance: HAInstance) -> set[Location] | HomeassistantAPIError:
    result = _with_client(instance, lambda client: client.get_entities())
    if isinstance(result, HomeassistantAPIError):
        return result
    zones = result.get("zone")
    if zones is None:
        return set()
    return {
        entity.state.attributes.get("friendly_name", id)
        for id, entity in zones.entities.items()
    }
