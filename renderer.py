from __future__ import annotations

import pygame
from math import pi, sin, cos

from homeassistant_api import HomeassistantAPIError
from locations import *


def _draw_slice(
    surface: pygame.surface.Surface,
    color: pygame.color.Color,
    rect: pygame.rect.Rect,
    start_angle: float,
    stop_angle: float,
):
    # radians between points on the circle's arc, should look ~smooth while being ~fast
    VERTEX_ANGLE = 2 * pi / 100
    radius_x, radius_y = (rect.width / 2, rect.height / 2)

    def point_at_angle(angle: float):
        return (
            rect.centerx + int(radius_x * cos(angle)),
            rect.centery - int(radius_y * sin(angle)),
        )

    vertices = [rect.center]
    angle = start_angle
    while angle < stop_angle:
        vertices.append(point_at_angle(angle))
        angle += VERTEX_ANGLE
    vertices.append(point_at_angle(stop_angle))
    pygame.draw.polygon(surface, color, vertices)
    pygame.draw.polygon(surface, (0, 0, 0), vertices, width=2)


def _render_wheel(surface: pygame.surface.Surface, zones: set[str]):
    arc_angle = 2 * pi / len(zones)
    even_colour = pygame.color.Color(150, 150, 0)
    odd_colour = pygame.color.Color(128, 128, 0)
    for i, _ in enumerate(zones):
        colour = even_colour if i % 2 == 0 else odd_colour
        left_angle = pi / 2 - i * arc_angle
        _draw_slice(
            surface,
            colour,
            surface.get_rect(),
            left_angle - arc_angle,
            left_angle,
        )

def _render_hands(
    surface: pygame.surface.Surface, 
    font: pygame.font.Font,
    people: set[PersonState],
    failures: dict[Person, HomeassistantAPIError],
):
    current_height = 0

    for person in people:
        text = font.render(
            f"{person.person.name}: {person.get_location()}", True, (0, 255, 0)
        )
        surface.blit(text, (0, current_height))
        current_height += font.get_height()

    for person, failure in failures.items():
        text = font.render(f"{person.name}: {failure}", True, (255, 0, 0))
        surface.blit(text, (0, current_height))
        current_height += font.get_height()


class Renderer:
    def __init__(self):
        pass

    def __enter__(self) -> Renderer:
        pygame.init()
        self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
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
        zones: set[str],
    ):
        self._screen.fill((0, 0, 0))
        _render_wheel(self._clock_surface, zones)
        _render_hands(self._screen, self._font, people, failures)
        pygame.display.flip()

    def should_exit(self) -> bool:
        events = pygame.event.get(eventtype=pygame.KEYDOWN)
        return any(event.key in {pygame.K_ESCAPE, pygame.K_q} for event in events)
