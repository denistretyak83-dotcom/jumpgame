"""Композиционные компоненты-поведения и протоколы для персонажей (R4).

Архитектура:
- Протоколы (DIP) — модель и View зависят от абстракций.
- DeathBehavior — ОПЦИОНАЛЬНЫЙ компонент смерти. Не задан => персонаж просто is_dead.
- RespawnBehavior — компонент возврата копии персонажа.
- Animatable — протокол View-слоя: модель НЕ тикает анимации (это делает
  SpriteCache.update(dt) в Game._update), а лишь отдаёт CharacterVisualState.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from views.character_view import CharacterVisualState


# ---------------------------------------------------------------------------
# ПРОТОКОЛ АНИМАЦИЙ (View-слой)
# ---------------------------------------------------------------------------
from typing import Any, Callable, Optional, Protocol, runtime_checkable


@runtime_checkable
class Animatable(Protocol):
    """Структурный протокол View-слоя.

    Протокол, а не ABC: модели НЕ обязаны наследоваться, достаточно
    структурного соответствия (есть facing_left, is_dead, get_visual_state).
    Это нужно, чтобы не блокировать инстанцирование Player/Enemy.
    """

    @property
    def facing_left(self) -> bool: ...

    @property
    def is_dead(self) -> bool: ...

    def get_visual_state(self) -> CharacterVisualState: ...
# ---------------------------------------------------------------------------
# ПРОТОКОЛ СМЕРТИ (опциональный компонент)
# ---------------------------------------------------------------------------
class DeathBehavior(ABC):
    """Поведение смерти (SRP + композиция).

    Опционально: если у персонажа нет death_behavior, он просто становится
    is_dead без кинематографичной сцены."""

    @abstractmethod
    def attach(self, owner: Any) -> None:
        """Привязывает поведение к владельцу (персонажу)."""

    @abstractmethod
    def die(self, launch_up: bool = True) -> None:
        """Инициирует сцену смерти."""

    @abstractmethod
    def update(self, dt: float) -> bool:
        """Тикает сцену смерти. Возвращает True, когда процесс завершён."""

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """True, пока сцена смерти ещё в процессе."""


# ---------------------------------------------------------------------------
# ПРОТОКОЛ ВОЗРОЖДЕНИЯ / КОПИРОВАНИЯ
# ---------------------------------------------------------------------------
class RespawnBehavior(ABC):
    """Поведение возврата копии персонажа (SRP)."""

    @abstractmethod
    def spawn_copy(self) -> Any:
        """Возвращает новую копию персонажа в исходной точке."""


# ---------------------------------------------------------------------------
# КОНКРЕТНЫЙ КОМПОНЕНТ: "кінематографична смерть-падение игрока"
# ---------------------------------------------------------------------------
class FallDeathBehavior(DeathBehavior):
    """Смерть-падение вниз с нарастающей скоростью.

    Владелец — персонаж (должен иметь атрибуты vel_x, rect).
    Параметры передаются явно из конфига (слабая связь). Падение завершается,
    когда верх персонажа уходит ниже screen_height + margin."""

    def __init__(self,
                 owner: Optional[Any] = None,
                 death_gravity: float = 1200,
                 screen_height: int = 720,
                 margin: int = 60,
                 launch_vy: float = -400,
                 fall_vy: float = -100):
        self.owner = owner
        self.death_gravity = death_gravity
        self.screen_height = screen_height
        self.margin = margin
        self.launch_vy = launch_vy
        self.fall_vy = fall_vy
        self.death_vy = 0.0
        self.active = False

    def attach(self, owner: Any) -> None:
        self.owner = owner

    def die(self, launch_up: bool = True) -> None:
        if self.owner is None:
            return
        self.active = True
        self.owner.vel_x = 0
        self.death_vy = self.launch_vy if launch_up else self.fall_vy

    def update(self, dt: float) -> bool:
        if not self.active or self.owner is None:
            return False
        self.death_vy += self.death_gravity * dt
        self.owner.rect.y += int(self.death_vy * dt)
        # Завершено: персонаж полностью упал за нижний край экрана (+запас)
        return self.owner.rect.top > self.screen_height + self.margin

    @property
    def is_active(self) -> bool:
        return self.active


# ---------------------------------------------------------------------------
# КОНКРЕТНЫЙ КОМПОНЕНТ: "вернуть копию через фабрику"
# ---------------------------------------------------------------------------
class CallableRespawnBehavior(RespawnBehavior):
    """Возвращает копию через переданную callable-фабрику.

    Фабрика захватывает нужные параметры (spawn_x/y, left/right, config),
    поэтому избегаем циклических импортов (enemy <-> behaviors)."""

    def __init__(self, factory: Callable[[], Any]):
        self._factory = factory

    def spawn_copy(self) -> Any:
        return self._factory()