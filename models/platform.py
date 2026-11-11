"""Platform -- типизированная платформа (Фаза 5, задача C).

Держит геометрию (core.geometry.RectPosition, без pygame) + стиль плитки
tile_style. Делегирует геометрия-свойства в self.rect и реализует rect4-протокол
(x, y, width, height) через __getitem__/__len__/__iter__, чтобы оставаться
совместимым с pygame.Rect.colliderect()/Rect() для физики и рендера.

Контракт (Фаза 5, OCP): тип/стиль платформы регистрируется через WorldFactory
(см. models/factory.py), сама модель не зависит от pygame в return-значениях.
"""

from dataclasses import dataclass

from core.geometry import RectPosition


@dataclass
class Platform:
    rect: RectPosition
    tile_style: str = "grass_top"

    # --- геометрия (делегирование в self.rect) ---
    @property
    def x(self) -> float:
        return self.rect.x

    @property
    def y(self) -> float:
        return self.rect.y

    @property
    def width(self) -> float:
        return self.rect.width

    @property
    def height(self) -> float:
        return self.rect.height

    @property
    def left(self) -> float:
        return self.rect.left

    @property
    def right(self) -> float:
        return self.rect.right

    @property
    def top(self) -> float:
        return self.rect.top

    @property
    def bottom(self) -> float:
        return self.rect.bottom

    @property
    def centerx(self) -> float:
        return self.rect.centerx

    @property
    def centery(self) -> float:
        return self.rect.centery

    # --- rect4-протокол (для pygame.Rect / colliderect совместимости) ---
    _geo_fields = ("x", "y", "width", "height")

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [getattr(self, f) for f in self._geo_fields][index]
        return getattr(self, self._geo_fields[index])

    def __len__(self) -> int:
        return 4

    def __iter__(self):
        return (getattr(self, f) for f in self._geo_fields)
