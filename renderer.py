from __future__ import annotations

import pygame

from pygame.math import Vector2
from math import pi

from homeassistant_api import HomeassistantAPIError

from config import Location
from snapshot import Snapshot
from rendering.util import blit_text_on_axis, lerp
from rendering.slice import Slice


class Renderer:
    def __init__(self, fullscreen: bool):
        self._fullscreen = fullscreen

    def __enter__(self) -> Renderer:
        pygame.init()
        if self._fullscreen:
            self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode((1200, 800), pygame.NOFRAME)

        # Make a square surface just for rendering the clock itself, for simpler dimensions
        clock_area = pygame.rect.Rect(0, 0, 1, 1).fit(self._screen.get_rect())
        clock_area.center = self._screen.get_rect().center
        self._clock_surface = self._screen.subsurface(clock_area)
        self._width = self._screen.get_width()
        self._height = self._screen.get_height()

        # TODO: more fonts
        self._font = pygame.font.SysFont("notosans.ttf", 24)

        return self

    def __exit__(self, *_):
        pygame.quit()

    def should_exit(self) -> bool:
        events = pygame.event.get(eventtype=pygame.KEYDOWN)
        return any(event.key in {pygame.K_ESCAPE, pygame.K_q} for event in events)

    def render(
        self,
        snapshot: Snapshot,
    ):
        if isinstance(snapshot.locations, HomeassistantAPIError):
            return
        if len(snapshot.locations) > 0:
            arc_angle = 2 * pi / len(snapshot.locations)
        else:
            arc_angle = 2 * pi

        slices = dict[Location, Slice]()
        for i, location in enumerate(snapshot.locations):
            stop_angle = -pi / 2 + i * arc_angle
            slices[location] = Slice(
                start_angle=stop_angle + arc_angle, stop_angle=stop_angle
            )

        self._screen.fill((0, 0, 0))
        self._render_wheel(slices)
        self._render_hands(snapshot, slices)
        self._render_errors(snapshot)
        pygame.display.flip()

    def _render_wheel(
        self,
        slices: dict[Location, Slice],
    ):
        surface = self._clock_surface
        # Make a smaller wheel area, so we can render the location labels outside it without
        # going off-screen.
        size = Vector2(surface.get_size())
        wheel_rect = surface.get_rect().inflate(-size * 0.1)
        wheel_surface = surface.subsurface(wheel_rect)

        even_colour = pygame.color.Color(150, 150, 0)
        odd_colour = pygame.color.Color(128, 128, 0)
        for i, (location, slice) in enumerate(slices.items()):
            colour = even_colour if i % 2 == 0 else odd_colour
            slice.draw(wheel_surface, colour)

            text = self._font.render(location, True, (255, 0, 0))
            blit_text_on_axis(
                surface,
                text,
                slice.middle_angle(),
                wheel_rect.width / 2 + self._font.get_height(),
            )

    def _render_hands(
        self,
        snapshot: Snapshot,
        slices: dict[Location, Slice],
    ):
        surface = self._clock_surface
        clock_radius = surface.get_rect().width * 0.9 / 2
        radius_range = (clock_radius * 0.1, clock_radius * 0.9)
        for i, person in enumerate(snapshot.people):
            slice = slices.get(person.location)
            if slice is None:
                continue
            text = self._font.render(person.name, True, (0, 255, 0))
            # Blit some distance up the hand
            blit_text_on_axis(
                surface,
                text,
                slice.middle_angle(),
                lerp(*radius_range, i / len(snapshot.people)),
            )

    def _render_errors(self, snapshot: Snapshot):
        current_height = 0
        for error in snapshot.get_error_strings():
            text = self._font.render(error, True, (255, 0, 0))
            self._screen.blit(text, (0, current_height))
            current_height += self._font.get_height()
