"""core/geometry.py — собственный геометрический объект без pygame.

Позволяет моделям работать с прямоугольником, не завися от pygame.Rect
(главный блокер масштабирования, раздел 4.1 плана).
View/рендер получает pygame.Rect по требованию через to_pygame_rect().
"""
from dataclasses import dataclass


@dataclass
class RectPosition:
    """Прямоугольник без зависимостей от pygame (x, y, width, height)."""
    x: float
    y: float
    width: float
    height: float

    # --- Вычисляемые свойства ---
    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def centerx(self) -> float:
        return self.x + self.width / 2

    @property
    def centery(self) -> float:
        return self.y + self.height / 2

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    def intersects(self, other: "RectPosition") -> bool:
        """Простое пересечение по AABB."""
        return (
            self.x < other.x + other.width
            and other.x < self.x + self.width
            and self.y < other.y + other.height
            and other.y < self.y + self.height
        )

    def contains_point(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.right) and (self.y <= py <= self.bottom)

    def to_pygame_rect(self):
        """Строит pygame.Rect по требованию (для View/рендера, не в моделях)."""
        import pygame
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
