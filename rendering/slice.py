import dataclasses
import pygame
from pygame.math import Vector2

from math import pi


@dataclasses.dataclass
class Slice:
    start_angle: float
    stop_angle: float

    def middle_angle(self) -> float:
        angle = (self.start_angle + self.stop_angle) / 2
        return angle

    def draw(self, surface: pygame.surface.Surface, color: pygame.color.Color):
        """Draw a color-filled slice of a circle."""
        # radians between points on the circle's arc, should look ~smooth while being ~fast
        VERTEX_ANGLE = 2 * pi / 100
        rect = surface.get_rect()
        center = Vector2(rect.center)
        radius = rect.width / 2

        def point_at_angle(angle: float) -> pygame.math.Vector2:
            return center + Vector2(radius, 0).rotate_rad(angle)

        vertices = [center]
        angle = self.start_angle
        while angle > self.stop_angle:
            vertices.append(point_at_angle(angle))
            angle -= VERTEX_ANGLE
        vertices.append(point_at_angle(self.stop_angle))
        # Draw the slice
        pygame.draw.polygon(surface, color, vertices)
        # Draw the border
        pygame.draw.polygon(surface, (0, 0, 0), vertices, width=2)
