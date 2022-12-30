import dataclasses

from homeassistant_api import Client, State, HomeassistantAPIError, processing

from typing import TypeVar, Callable

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

    def get_image(self) -> Optional[str] | HomeassistantAPIError:
        path = self.get_image_path()
        if path is None:
            return None
        path = path.removeprefix("/api/")

        data = _with_client(
            self.instance, lambda client: client.request(path, decode_bytes=False)
        )
        return data


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
) -> tuple[dict[PersonState, Location], dict[PersonState, HomeassistantAPIError]]:
    successes = {}
    failures = {}

    for instance, people in sources.items():

        def fn(client: Client):
            for person in people:
                try:
                    successes[person] = get_person_state_from_client(client, person)
                except HomeassistantAPIError as e:
                    failures[person] = e

        result = _with_client(instance, fn)
        if isinstance(result, HomeassistantAPIError):
            # If the client itself fails creation, then mark all associated people as errored.
            failures.update({person: result for person in people})

    return (successes, failures)
