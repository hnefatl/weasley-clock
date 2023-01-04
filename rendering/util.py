import pygame
from pygame.math import Vector2

from math import fmod, pi, degrees

def normalize_radians(rad: float) -> float:
    """Normalize into range [-pi, pi)"""
    return fmod(rad + pi, 2 * pi) - pi


def lerp(start: float, end: float, percent: float) -> float:
    return start + (end - start) * percent

def blit_on_axis(
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


def blit_text_on_axis(
    surface: pygame.surface.Surface,
    image: pygame.surface.Surface,
    angle: float,
    radius: float,
):
    """Blit text on an axis, flipping it right-way-up if it would be upside-down."""
    if normalize_radians(angle) > 0:
        # Render the text on the bottom of the wheel "upside down" for easier reading.
        image = pygame.transform.rotate(image, 180)
    blit_on_axis(surface, image, angle, radius)

