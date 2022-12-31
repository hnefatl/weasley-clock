from __future__ import annotations

from config import *
from locations import *
from renderer import *


def main(renderer: Renderer):
    sources = load_sources()

    while True:
        successes, failures = get_person_states(sources)
        if renderer.should_exit():
            break
        renderer.render(successes, failures, {'foo', 'bar', 'baz', 'bing', 'bap'})


if __name__ == "__main__":
    with Renderer() as renderer:
        main(renderer)

