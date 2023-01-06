from __future__ import annotations

import argparse
import pathlib
from typing import Optional

from config import load_config, Config
from snapshot import fetch_snapshot
from renderer import Renderer
from mock_data import get_mock_data


def main(renderer: Renderer, use_mock_data: bool, config_file: pathlib.Path):
    config: Optional[Config] = None

    while True:
        if renderer.should_exit():
            break

        if use_mock_data:
            snapshot = get_mock_data()
        else:
            if config is None:
                config = load_config(config_file)
            snapshot = fetch_snapshot(config)

        renderer.render(snapshot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fullscreen", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--use_mock_data", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--config_file", default="config.json"
    )
    args = parser.parse_args()

    with Renderer(fullscreen=args.fullscreen) as renderer:
        main(renderer, args.use_mock_data, pathlib.Path(args.config_file))
