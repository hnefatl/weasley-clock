from __future__ import annotations

import argparse
from typing import Iterable

from homeassistant_api import HomeassistantAPIError

from config import HAInstance, load_sources
from locations import Location, get_person_states, get_all_locations
from renderer import Renderer


class AllLocations:
    def __init__(self):
        self._state = dict[HAInstance, set[Location] | HomeassistantAPIError]()

    def update(self, instances: Iterable[HAInstance]) -> set[Location]:
        for instance in instances:
            result = get_all_locations(instance)
            if isinstance(result, set):
                self._state[instance] = result
        return self.get_locations()

    def get_locations(self) -> set[Location]:
        return set[Location]().union(
            *[
                locations
                for locations in self._state.values()
                if isinstance(locations, set)
            ]
        )

    def get_errored_instances(self) -> dict[HAInstance, HomeassistantAPIError]:
        return {
            instance: state
            for instance, state in self._state.items()
            if isinstance(state, HomeassistantAPIError)
        }


def main(renderer: Renderer):
    sources = load_sources()

    all_locations = AllLocations()

    while True:
        successes, failures = get_person_states(sources)
        locations = all_locations.update(sources.keys())
        if renderer.should_exit():
            break
        renderer.render(successes, failures, locations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--fullscreen', action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    with Renderer(fullscreen=args.fullscreen) as renderer:
        main(renderer)
