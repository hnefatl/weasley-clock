from __future__ import annotations

import argparse

from config import load_config
from snapshot import fetch_snapshot
from renderer import Renderer
from mock_data import get_mock_data


def main(renderer: Renderer, use_mock_data: bool):
    config = load_config()

    while True:
        if renderer.should_exit():
            break
        snapshot = get_mock_data() if use_mock_data else fetch_snapshot(config)
        renderer.render(snapshot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fullscreen", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--use_mock_data", action=argparse.BooleanOptionalAction, default=False
    )
    args = parser.parse_args()

    with Renderer(fullscreen=args.fullscreen) as renderer:
        main(renderer, args.use_mock_data)
