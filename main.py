from __future__ import annotations

from typing import Mapping, Optional, Union, DefaultDict

from config import *
from locations import *


def main():
    sources = load_sources()

    successes, failures = get_person_states(sources)
    for person, error in failures.items():
        print(f"{person.name}: Error: {error}")

    for person, person_state in successes.items():
        image = person_state.get_image()
        print(f"{person.name} ({person_state.get_image_path()}): {person_state.get_location()}")


if __name__ == "__main__":
    main()
