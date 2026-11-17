"""playable_character.py — контракт управляемого персонажа (DIP/ISP).

Задача Фазы 12: любой герой (Player и будущие новые герои) реализует
единый контракт PlayableCharacter, чтобы Game/WorldFactory/LevelFlow
работали с ним через абстракцию, а не через конкретный класс.

Это Protocol (structural subtyping): классу не нужно наследовать его —
достаточно иметь требуемые атрибуты/методы. Проверяется через isinstance().
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.geometry import RectPosition
from models.model_state import ModelVisualData


@runtime_checkable
class PlayableCharacter(Protocol):
    """Что значит «управляемый персонаж».

    Объединяет физическое тело (PhysicsBody) и обработку игрового ввода
    (intent). Зависимые модули (Game._update, WorldFactory, LevelFlow)
    опираются только на этот контракт.
    """

    # --- физическое тело ---
    rect: RectPosition
    vel_x: float
    vel_y: float
    on_ground: bool
    is_dead: bool

    # --- гейм-цикл ---
    def update(self, dt, ctx=None, intent=None) -> None: ...

    def apply_physics(self, dt, platforms) -> bool:
        """Применить физику; True — удар головой."""

    def get_visual_data(self) -> ModelVisualData:
        """Чистые факты состояния (без pygame)."""

    # --- жизненный цикл ---
    def die(self, launch_up: bool = True) -> None: ...

    def spawn_copy(self): ...
