"""Фреймворк поведения врагов (этапы в2-в4).

Композиция вместо наследования: поведение вынесено из Enemy в отдельные
классы-поведения, выбираемые по ключу "behavior" через EnemyBehaviorRegistry
(OCP). Реализованы:

- WalkerBehavior  — X-патруль между bound_left/bound_right.
- ChaserBehavior  — преследование игрока по X (через ctx.player_x).
- FlyerBehavior   — лётун/hover: X-патруль + вертикальная синусоида вокруг
                    базовой Y. Платформы и гравитацию ИГНОРИРУЕТ (в4 1а/2б).
"""

import math
from abc import ABC, abstractmethod
from collections.abc import Callable


class EnemyBehavior(ABC):
    """Интерфейс поведения врага."""

    @abstractmethod
    def attach(self, enemy) -> None:
        """Привязать поведение к врагу."""

    @abstractmethod
    def update(self, enemy, dt, ctx=None, intent=None) -> None:
        """Обновить врага на один кадр."""


class WalkerBehavior(EnemyBehavior):
    """Базовое патрулирование: движение вдоль оси X между границами."""

    def __init__(self):
        self._enemy = None

    def attach(self, enemy) -> None:
        self._enemy = enemy

    def update(self, enemy, dt, ctx=None, intent=None) -> None:
        pos = enemy.pos_x + enemy.vel_x * dt
        if pos < enemy.bound_left:
            overrun = enemy.bound_left - pos
            pos = enemy.bound_left + overrun
            enemy.vel_x = abs(enemy.vel_x)
        elif pos + enemy.rect.width > enemy.bound_right:
            overrun = (pos + enemy.rect.width) - enemy.bound_right
            pos = enemy.bound_right - enemy.rect.width - overrun
            enemy.vel_x = -abs(enemy.vel_x)

        enemy.pos_x = pos
        enemy.rect.x = int(round(enemy.pos_x))


class ChaserBehavior(EnemyBehavior):
    """Преследование игрока по X в пределах границ патруля."""

    def __init__(self):
        self._enemy = None

    def attach(self, enemy) -> None:
        self._enemy = enemy

    def update(self, enemy, dt, ctx=None, intent=None) -> None:
        if ctx is None or not hasattr(ctx, "player_x"):
            self._walker_fallback(enemy, dt)
            return

        player_x = float(ctx.player_x)
        if player_x < enemy.pos_x:
            direction = -1
        elif player_x > enemy.pos_x:
            direction = 1
        else:
            direction = 0

        pos = enemy.pos_x + direction * enemy.vel_x * dt
        if pos < enemy.bound_left:
            pos = enemy.bound_left
        elif pos + enemy.rect.width > enemy.bound_right:
            pos = enemy.bound_right - enemy.rect.width

        enemy.pos_x = pos
        enemy.rect.x = int(round(enemy.pos_x))

    def _walker_fallback(self, enemy, dt) -> None:
        pos = enemy.pos_x + enemy.vel_x * dt
        if pos < enemy.bound_left:
            overrun = enemy.bound_left - pos
            pos = enemy.bound_left + overrun
            enemy.vel_x = abs(enemy.vel_x)
        elif pos + enemy.rect.width > enemy.bound_right:
            overrun = (pos + enemy.rect.width) - enemy.bound_right
            pos = enemy.bound_right - enemy.rect.width - overrun
            enemy.vel_x = -abs(enemy.vel_x)
        enemy.pos_x = pos
        enemy.rect.x = int(round(enemy.pos_x))


class FlyerBehavior(EnemyBehavior):
    """Летающий враг (hover): X-патруль + вертикальная синусоида.

    НЕ падает, НЕ сталкивается с платформами, без гравитации/физики.
    Движется по X как патруль, а Y меняется синусоидально вокруг базовой Y.
    Синхронизирует и rect.x, и rect.y.
    """

    def __init__(self, amplitude=30, frequency=2.0):
        self._enemy = None
        self.amplitude = amplitude
        self.frequency = frequency
        self._time = 0.0
        self._base_y = 0.0

    def attach(self, enemy) -> None:
        self._enemy = enemy
        self._base_y = float(enemy.rect.y)

    def update(self, enemy, dt, ctx=None, intent=None) -> None:
        # --- X-движение (патруль) ---
        pos_x = enemy.pos_x + enemy.vel_x * dt
        if pos_x < enemy.bound_left:
            overrun = enemy.bound_left - pos_x
            pos_x = enemy.bound_left + overrun
            enemy.vel_x = abs(enemy.vel_x)
        elif pos_x + enemy.rect.width > enemy.bound_right:
            overrun = (pos_x + enemy.rect.width) - enemy.bound_right
            pos_x = enemy.bound_right - enemy.rect.width - overrun
            enemy.vel_x = -abs(enemy.vel_x)

        # --- Y-движение (синусоида) ---
        self._time += dt
        offset = self.amplitude * math.sin(2 * math.pi * self.frequency * self._time)
        pos_y = self._base_y + offset

        # --- Синхронизация rect из float-позиции ---
        enemy.pos_x = pos_x
        enemy.pos_y = pos_y
        enemy.rect.x = int(round(enemy.pos_x))
        enemy.rect.y = int(round(enemy.pos_y))


class EnemyBehaviorRegistry:
    """Реестр "тип поведения -> фабрика поведения" (OCP)."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], EnemyBehavior]] = {}
        self._fallback_type = "walker"

    def register(self, behavior_type: str, behavior_factory: Callable[[], EnemyBehavior]) -> None:
        self._factories[behavior_type] = behavior_factory

    def create(self, behavior_type: str | None = None) -> EnemyBehavior:
        return self._factories.get(behavior_type or "", self._factories[self._fallback_type])()


# Локальный реестр по умолчанию (fallback при отсутствии DI-реестра).
DEFAULT_BEHAVIOR_REGISTRY = EnemyBehaviorRegistry()
DEFAULT_BEHAVIOR_REGISTRY.register("walker", WalkerBehavior)
DEFAULT_BEHAVIOR_REGISTRY.register("chaser", ChaserBehavior)
DEFAULT_BEHAVIOR_REGISTRY.register("flyer", FlyerBehavior)
