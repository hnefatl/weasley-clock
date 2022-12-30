from __future__ import annotations

from typing import Mapping, Optional, Union, DefaultDict

from config import *
from locations import get_locations


def main():
    config = load_config()

    for person, location in get_locations(config).items():
        print(f"{person.name}: {location}")


if __name__ == "__main__":
    main()
