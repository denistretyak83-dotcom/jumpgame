from abc import ABC, abstractmethod

from core.event_bus import GameEvents
from models.behaviors import DeathBehavior, RespawnBehavior
from models.entity import Entity
from models.model_state import ModelVisualData
from models.physics import PhysicsComponent


class BaseCharacter(Entity, ABC):

    def __init__(self, x: int, y: int, width: int, height: int,
                 config=None, event_bus=None,
                 death_behavior: DeathBehavior | None = None,
                 respawn_behavior: RespawnBehavior | None = None):
        super().__init__(x, y, width, height)
        self.event_bus = event_bus
        self._cfg = config

        # --- состояние ---
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_left = False
        self.is_dead = False

        # --- композиция: физика (R1) + поведенческие компоненты (R4) ---
        self.physics = PhysicsComponent(config)
        self.death_behavior = None
        self.respawn_behavior = None
        if death_behavior is not None:
            death_behavior.attach(self)
            self.death_behavior = death_behavior
        self.respawn_behavior = respawn_behavior

    # ------------------------- абстракции -------------------------
    @abstractmethod
    def update(self, dt, ctx=None, intent=None) -> None:
        ...

    @abstractmethod
    def get_visual_data(self) -> ModelVisualData:
        """Возвращает чистые факты состояния модели (без pygame и View).

        View (CharacterView.build_state) превратит их в кадр.
        """

    # ------------------------- физика -------------------------
    def apply_physics(self, dt, platforms) -> bool:
        """Применяет физику через PhysicsComponent. True — был удар головой."""
        return self.physics.apply(self, dt, platforms)

    # ------------------------- СМЕРТЬ (прокси на компонент) -------------------------
    def die(self, launch_up: bool = True) -> None:
        """Инициирует смерть. Если death_behavior не задан — просто помечаем is_dead."""
        if self.is_dead:
            return
        self.is_dead = True
        if self.death_behavior is not None:
            self.death_behavior.die(launch_up)
        if self.event_bus:
            self.event_bus.emit(GameEvents.CHARACTER_DEATH, self)

    def update_death(self, dt: float) -> bool:
        """Тикает сцену смерти. Возвращает True, когда она завершена (выпал за экран)."""
        if self.death_behavior is not None:
            return self.death_behavior.update(dt)
        return False

    # ------------------------- ВОЗРОЖДЕНИЕ (прокси на компонент) -------------------------
    def spawn_copy(self):
        """Возвращает копию персонажа. Без respawn_behavior — сам объект
        (базовое поведение Player, совместимое со старой реализацией)."""
        if self.respawn_behavior is not None:
            return self.respawn_behavior.spawn_copy()
        return self
