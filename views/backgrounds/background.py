"""
views/backgrounds/background.py — контракт фона (ФР-4).

Renderer зависит от абстракции Background, а не от конкретной реализации.
Это позволяет подменять фон (parallax / procedural / PNG) без правки Renderer
(OCP/DIP).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Background(Protocol):
    """Что умеет любой фон: обновляться под игрока и рисоваться."""

    def update(self, player_x, scroll_speed: float = 1) -> None:
        """Обновить позицию фона под игрока (для параллакса)."""

    def draw(self, screen, player_x) -> None:
        """Нарисовать фон на screen с учётом позиции игрока."""

    @property
    def layers(self) -> list:
        """Вернуть список слоёв фона (для инспекции/тестов)."""
        ...
