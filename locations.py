from homeassistant_api import Client, State, HomeassistantAPIError

from config import *

Location = str


def _get_location_from_person(person: State) -> Location:
    state = person.state
    SPECIAL_LOCATIONS = {
        "Away": "Elsewhere",
    }
    return SPECIAL_LOCATIONS.get(state, state)


def get_locations(
    sources: Sources,
) -> dict[Person, Union[Location, HomeassistantAPIError]]:
    results = {}
    for client, people in sources.items():
        try:
            with Client(api_url=client.url, token=client.token) as client:
                for person in people:
                    try:
                        results[person] = _get_location_from_person(
                            client.get_state(entity_id=person.id)
                        )
                    except HomeassistantAPIError as e:
                        results[person] = e
        except HomeassistantAPIError as e:
            # If the client itself fails creation, then mark all associated people as errored.
            results.update({person: e for person in people})
    return results
