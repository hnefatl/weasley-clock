from homeassistant_api import HomeassistantAPIError

from config import ConfigPerson
from snapshot import Snapshot, Person


def get_mock_data() -> Snapshot:
    locations = ["Home", "Office", "Shops", "Mars", "Moon"]

    mock_people = {
        Person(
            name="Keith",
            id="person.keith",
            instance_url="mock.example.com",
            location=locations[0],
            photo_url="",
            photo=HomeassistantAPIError("mock photo missing"),
        ),
        Person(
            name="Jennifer",
            id="person.jennifer",
            instance_url="mock.example.com",
            location=locations[1],
            photo_url="",
            photo=HomeassistantAPIError("mock photo missing"),
        ),
        Person(
            name="Bill",
            id="person.bill",
            instance_url="mock.example.com",
            location=locations[1],
            photo_url="",
            photo=HomeassistantAPIError("mock photo missing"),
        ),
        Person(
            name="Jensen",
            id="person.jensen",
            instance_url="mock.example.com",
            location=locations[2],
            photo_url="",
            photo=HomeassistantAPIError("mock photo missing"),
        ),
        Person(
            name="Janet",
            id="person.janet",
            instance_url="mock.example.com",
            location="Nonexistent location",
            photo_url="",
            photo=HomeassistantAPIError("mock photo missing"),
        ),
    }
    return Snapshot(
        people=mock_people,
        locations=set(locations),
        errored_people={
            ConfigPerson(  # pyright: ignore[reportGeneralTypeIssues]
                name="Eli", id="person.eli"
            ): HomeassistantAPIError("HA error")
        },
        errored_instances={}
    )
