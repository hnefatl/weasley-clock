from __future__ import annotations

import dataclasses
import pygame

from pygame.math import Vector2
from math import pi, degrees, fmod

from homeassistant_api import HomeassistantAPIError

from config import Location
from snapshot import Snapshot


@dataclasses.dataclass
class Slice:
    start_angle: float
    stop_angle: float

    def middle_angle(self) -> float:
        angle = (self.start_angle + self.stop_angle) / 2
        return angle


def normalize_radians(rad: float) -> float:
    """Normalize into range [-pi, pi)"""
    return fmod(rad + pi, 2 * pi) - pi


def lerp(start: float, end: float, percent: float) -> float:
    return start + (end - start) * percent


def _draw_slice(
    surface: pygame.surface.Surface,
    color: pygame.color.Color,
    slice: Slice,
):
    """Draw a color-filled slice of a circle."""
    # radians between points on the circle's arc, should look ~smooth while being ~fast
    VERTEX_ANGLE = 2 * pi / 100
    rect = surface.get_rect()
    center = Vector2(rect.center)
    radius = rect.width / 2

    def point_at_angle(angle: float) -> pygame.math.Vector2:
        return center + Vector2(radius, 0).rotate_rad(angle)

    vertices = [center]
    angle = slice.start_angle
    while angle > slice.stop_angle:
        vertices.append(point_at_angle(angle))
        angle -= VERTEX_ANGLE
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
    """Blit an image rotated to lie on an axis from the centre of the surface."""
    # Rotate the assumed-horizontal image to be at 0 radians (right side of the clock)
    image = pygame.transform.rotate(image, -90 - degrees(angle))

    # vector to the centre of the image
    axis = Vector2(radius, 0)
    axis.rotate_rad_ip(angle)

    surface_center = Vector2(surface.get_rect().center)
    # Generate a new bounding rect for the rotated image, centered on the axis
    rotated_bounds = image.get_rect(center=surface_center + axis)

    surface.blit(image, rotated_bounds)


def _blit_text_on_axis(
    surface: pygame.surface.Surface,
    image: pygame.surface.Surface,
    angle: float,
    radius: float,
):
    """Blit text on an axis, flipping it right-way-up if it would be upside-down."""
    if normalize_radians(angle) > 0:
        # Render the text on the bottom of the wheel "upside down" for easier reading.
        image = pygame.transform.rotate(image, 180)
    _blit_on_axis(surface, image, angle, radius)


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
            _draw_slice(wheel_surface, colour, slice)

            text = self._font.render(location, True, (255, 0, 0))
            _blit_text_on_axis(
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
            _blit_text_on_axis(
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
