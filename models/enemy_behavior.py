"""Фреймворк поведения врагов (этап в2).

Композиция вместо наследования: поведение вынесено из Enemy в отдельные
классы-поведения, выбираемые по ключу данных "behavior" врага через
EnemyBehaviorRegistry (OCP). Новый вид поведения (chaser/turret) добавляется
регистрацией в реестре, без правки существующего кода Enemy.

ВАЖНО про выбор поведения: поведение выбирается по ОТДЕЛЬНОМУ ключу "behavior"
(значение по умолчанию — "walker"), а НЕ по "type" (который у врага в уровнях
равен "enemy" — это тип сущности для WorldFactory).
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional


class EnemyBehavior(ABC):
    """Интерфейс поведения врага."""

    @abstractmethod
    def attach(self, enemy) -> None:
        """Привязать поведение к врагу."""

    @abstractmethod
    def update(self, enemy, dt, ctx=None, intent=None) -> None:
        """Обновить врага на кадр."""


class WalkerBehavior(EnemyBehavior):
    """Базовое патрулирование: движение вдоль оси X между границами."""

    def __init__(self):
        self._enemy = None

    def attach(self, enemy):
        self._enemy = enemy

    def update(self, enemy, dt, ctx=None, intent=None):
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
        # ВАЖНО: синхронизация rect (иначе враг "замрёт" на экране)
        enemy.rect.x = int(round(enemy.pos_x))


class ChaserBehavior(EnemyBehavior):
    """Преследование игрока по оси X, ограниченное границами патруля.

    Враг двигается в сторону игрока (ctx.player_x) со своей скоростью,
    но не выходит за bound_left/bound_right. Если граница достигнута,
    враг останавливается у края (не стоит зеркально разворачивать —
    преследователь просто упёрся в границу).
    """

    def __init__(self):
        self._enemy = None

    def attach(self, enemy):
        self._enemy = enemy

    def update(self, enemy, dt, ctx=None, intent=None):
        # Определяем направление к игроку (если игрок доступен)
        if ctx is None or not hasattr(ctx, "player_x"):
            # Нет данных об игроке — ведём себя как walker (безопасный fallback)
            self._walker_fallback(enemy, dt)
            return

        player_x = ctx.player_x
        # Направление: -1 (влево) / 0 (на месте) / +1 (вправо)
        direction = 0
        if player_x < enemy.pos_x:
            direction = -1
        elif player_x > enemy.pos_x:
            direction = +1

        # Двигаемся с учётом скорости и границ
        pos = enemy.pos_x + direction * enemy.vel_x * dt

        # Ограничиваем границами патруля (не даём улететь за край)
        if pos < enemy.bound_left:
            pos = enemy.bound_left
        elif pos + enemy.rect.width > enemy.bound_right:
            pos = enemy.bound_right - enemy.rect.width

        enemy.pos_x = pos
        # ВАЖНО: синхронизация rect
        enemy.rect.x = int(round(enemy.pos_x))

    def _walker_fallback(self, enemy, dt):
        """Запасное поведение, если игрок недоступен (как walker)."""
        pos = enemy.pos_x + enemy.vel_x * dt
        if pos < enemy.bound_left:
            pos = enemy.bound_left
            enemy.vel_x = abs(enemy.vel_x)
        elif pos + enemy.rect.width > enemy.bound_right:
            pos = enemy.bound_right - enemy.rect.width
            enemy.vel_x = -abs(enemy.vel_x)
        enemy.pos_x = pos
        enemy.rect.x = int(round(enemy.pos_x))


class EnemyBehaviorRegistry:
    """Реестр "тип поведения -> фабрика поведения" (OCP)."""

    def __init__(self):
        self._factories: Dict[str, Callable[[], EnemyBehavior]] = {}
        self._fallback_type = "walker"

    def register(self, behavior_type, behavior_factory):
        self._factories[behavior_type] = behavior_factory

    def create(self, behavior_type=None):
        return self._factories.get(behavior_type or "",
                                   self._factories[self._fallback_type])()


DEFAULT_BEHAVIOR_REGISTRY = EnemyBehaviorRegistry()
DEFAULT_BEHAVIOR_REGISTRY.register("walker", WalkerBehavior)
DEFAULT_BEHAVIOR_REGISTRY.register("chaser", ChaserBehavior)