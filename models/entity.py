"""Base Entity -- shared position/size/collision box."""
import pygame


class Entity:
    """Base class for anything with a position, size, and collider."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, value):
        self.rect.x = value

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, value):
        self.rect.y = value
