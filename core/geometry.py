"""core/geometry.py — собственный геометрический объект без pygame.

Позволяет моделям работать с прямоугольником, не завися от pygame.Rect
(главный блокер масштабирования, раздел 4.1 плана).
View/рендер получает pygame.Rect по требованию через to_pygame_rect().

Свойства left/top/right/bottom/centerx/centery имеют и геттеры, и сеттеры —
это сохраняет публичный контракт pygame.Rect (правка/центрирование двигают
позицию, не меняя размер). Также реализованы colliderect()/move()/move_ip(),
copy() — для совместимости с pygame-интерфейсом, который ждут модель и тесты.
"""

from dataclasses import dataclass


@dataclass
class RectPosition:
    """Прямоугольник без зависимостей от pygame (x, y, width, height)."""

    x: float
    y: float
    width: float
    height: float

    # --- Вычисляемые свойства (аналог pygame.Rect: right/bottom/center/left/top) ---

    @property
    def right(self) -> float:
        return self.x + self.width

    @right.setter
    def right(self, value: float) -> None:
        self.x = value - self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @bottom.setter
    def bottom(self, value: float) -> None:
        self.y = value - self.height

    @property
    def centerx(self) -> float:
        return self.x + self.width / 2

    @centerx.setter
    def centerx(self, value: float) -> None:
        self.x = value - self.width / 2

    @property
    def centery(self) -> float:
        return self.y + self.height / 2

    @centery.setter
    def centery(self, value: float) -> None:
        self.y = value - self.height / 2

    @property
    def left(self) -> float:
        return self.x

    @left.setter
    def left(self, value: float) -> None:
        self.x = value

    @property
    def top(self) -> float:
        return self.y

    @top.setter
    def top(self, value: float) -> None:
        self.y = value

    # --- Методы (совместимы с интерфейсом pygame.Rect) ---

    def intersects(self, other: "RectPosition") -> bool:
        """Простое пересечение по AABB."""
        return (
            self.x < other.x + other.width
            and other.x < self.x + self.width
            and self.y < other.y + other.height
            and other.y < self.y + self.height
        )

    def colliderect(self, other: "RectPosition") -> bool:
        """Алиас intersects(): True, если прямоугольники пересекаются (AABB)."""
        return self.intersects(other)

    def move(self, dx: float, dy: float) -> "RectPosition":
        """Новый RectPosition со смещением на (dx, dy); исходник не меняется."""
        return RectPosition(self.x + dx, self.y + dy, self.width, self.height)

    def move_ip(self, dx: float, dy: float) -> "RectPosition":
        """Сместить координаты на (dx, dy) in place; возвращает self."""
        self.x += dx
        self.y += dy
        return self

    def copy(self) -> "RectPosition":
        """Копия прямоугольника (те же координаты и размер)."""
        return RectPosition(self.x, self.y, self.width, self.height)

    def contains_point(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.right) and (self.y <= py <= self.bottom)

    def to_pygame_rect(self):
        """Строит pygame.Rect по требованию (для View/рендера, не в моделях)."""
        import pygame

        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
