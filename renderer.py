from __future__ import annotations

import pygame
from pygame.math import Vector2
from math import pi, sin, cos, degrees

from homeassistant_api import HomeassistantAPIError
from locations import *


@dataclasses.dataclass
class Slice:
    start_angle: float
    stop_angle: float

    def middle_angle(self) -> float:
        return (self.start_angle + self.stop_angle) / 2


def _draw_slice(
    surface: pygame.surface.Surface,
    color: pygame.color.Color,
    slice: Slice,
):
    # radians between points on the circle's arc, should look ~smooth while being ~fast
    VERTEX_ANGLE = 2 * pi / 100
    rect = surface.get_rect()
    center = Vector2(rect.center)
    radius = rect.width / 2

    def point_at_angle(angle: float) -> pygame.math.Vector2:
        return center + Vector2(radius, 0).rotate_rad(angle)

    vertices = [center]
    angle = slice.start_angle
    while angle < slice.stop_angle:
        vertices.append(point_at_angle(angle))
        angle += VERTEX_ANGLE
    vertices.append(point_at_angle(slice.stop_angle))
    # Draw the slice
    pygame.draw.polygon(surface, color, vertices)
    # Draw the border
    pygame.draw.polygon(surface, (0, 0, 0), vertices, width=2)


def _blit_on_axis(
    surface: pygame.surface.Surface,
    image: pygame.surface.Surface,
    angle: float,
    radius: float,
):
    # Rotate the assumed-horizontal image to be at 0 radians (right side of the clock)
    image = pygame.transform.rotate(image, -90 - degrees(angle))

    # vector to the centre of the image
    axis = Vector2(radius, 0)
    axis = axis.rotate_rad(angle)

    surface_center = Vector2(surface.get_rect().center)
    # Generate a new bounding rect for the rotated image, centered on the axis
    rotated_bounds = image.get_rect(center=surface_center + axis)

    surface.blit(image, rotated_bounds)


def _render_wheel(
    surface: pygame.surface.Surface,
    font: pygame.font.Font,
    slices: dict[Location, Slice],
):
    even_colour = pygame.color.Color(150, 150, 0)
    odd_colour = pygame.color.Color(128, 128, 0)
    for i, (location, slice) in enumerate(slices.items()):
        colour = even_colour if i % 2 == 0 else odd_colour
        _draw_slice(surface, colour, slice)

        _blit_on_axis(
            surface,
            font.render(location, True, (255, 0, 0)),
            slice.middle_angle(),
            surface.get_rect().width / 2 + font.get_height(),
        )


def _render_hands(
    surface: pygame.surface.Surface,
    font: pygame.font.Font,
    people: set[PersonState],
    failures: dict[Person, HomeassistantAPIError],
    slices: dict[Location, Slice],
):
    current_height = 0

    for person in people:
        slice = slices[person.get_location()]
        text = font.render(person.person.name, True, (0, 255, 0))
        pygame.transform.rotate(text, slice.middle_angle())
        surface.blit(text, (0, current_height))
        current_height += font.get_height()

    for person, failure in failures.items():
        text = font.render(f"{person.name}: {failure}", True, (255, 0, 0))
        surface.blit(text, (0, current_height))
        current_height += font.get_height()


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

    def render(
        self,
        people: set[PersonState],
        failures: dict[Person, HomeassistantAPIError],
        locations: set[Location],
    ):
        if len(locations) > 0:
            arc_angle = 2 * pi / len(locations)
        else:
            arc_angle = 2 * pi

        slices = dict[Location, Slice]()
        for i, location in enumerate(locations):
            stop_angle = pi / 2 - i * arc_angle
            slices[location] = Slice(
                start_angle=stop_angle - arc_angle, stop_angle=stop_angle
            )

        self._screen.fill((0, 0, 0))
        _render_wheel(self._clock_surface, self._font, slices)
        _render_hands(self._screen, self._font, people, failures, slices)
        pygame.display.flip()

    def should_exit(self) -> bool:
        events = pygame.event.get(eventtype=pygame.KEYDOWN)
        return any(event.key in {pygame.K_ESCAPE, pygame.K_q} for event in events)
