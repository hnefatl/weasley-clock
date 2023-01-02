from homeassistant_api import HomeassistantAPIError, State

import dataclasses

from config import HAInstance, Person
from locations import Location, PersonState


@dataclasses.dataclass
class MockPerson:
    person: Person
    location: Location


def get_mock_data() -> tuple[
    set[PersonState], dict[Person, HomeassistantAPIError], set[Location]
]:
    locations = ["Home", "Office", "Shops", "Mars", "Moon"]

    mock_people = [
        MockPerson(
            person=Person(id="person.keith", name="Keith"), location=locations[0]
        ),
        MockPerson(
            person=Person(id="person.jennifer", name="Jennifer"), location=locations[1]
        ),
        MockPerson(person=Person(id="person.bill", name="Bill"), location=locations[1]),
        MockPerson(
            person=Person(id="person.jensen", name="Jensen"), location=locations[2]
        ),
    ]
    instance = HAInstance(url="https://mock.example.com", token="fake_token")
    return (
        {
            PersonState(
                p.person,
                instance,
                State(
                    entity_id=p.person.id,
                    state=p.location.capitalize(),
                    attributes={"location": p.location},
                    context=None,
                ),
            )
            for p in mock_people
        },
        {
            Person(  # pyright: ignore[reportGeneralTypeIssues]
                name="Unknown Bob", id="person.unknown_bob"
            ): HomeassistantAPIError("I'm a HA error")
        },
        set(locations),
    )
