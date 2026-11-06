from abc import ABC, abstractmethod
import pygame
from models.entity import Entity
from models.physics import PhysicsComponent
from views.character_view import CharacterVisualState


class BaseCharacter(Entity, ABC):
    """Чистая модель: состояние + физика + смерть.

    БЕЗ знания о спрайтах/анимациях (View-слой: SpriteCache/CharacterView).
    БЕЗ синглтон-зависимости от конфига (DI через параметр config).
    """

    def __init__(self, x, y, width, height, config=None,
                 event_bus=None, death_gravity=1200):
        super().__init__(x, y, width, height)
        self.event_bus = event_bus
        self._cfg = config
        self.death_gravity = death_gravity
        self.death_vy = 0
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_left = False
        self.is_dead = False

        # Физика: отдельный компонент (композиция)
        self.physics = PhysicsComponent(config)

    @abstractmethod
    def update(self, dt, ctx, intent=None):
        ...

    @abstractmethod
    def get_visual_state(self) -> CharacterVisualState:
        """Возвращает ЛОГИЧЕСКОЕ состояние для отрисовки.

        View (CharacterView) превратит его в кадр. Модель НЕ знает
        о спрайтах, flip и размерах картинок.
        """
        ...

    # ------------------------------------------------------------------
    # Физика через компонент (фасад для обратной совместимости)
    # ------------------------------------------------------------------

    def apply_physics(self, dt, platforms):
        """Применяет физику через PhysicsComponent.

        Returns:
            bool: True, если был удар головой о низ платформы.
        """
        return self.physics.apply(self, dt, platforms)

    # ------------------------------------------------------------------
    # Смерть (кинематографичное падение)
    # ------------------------------------------------------------------

    def die(self, launch_up=True):
        if self.is_dead:
            return
        self.is_dead = True
        self.vel_x = 0
        self.death_vy = -400 if launch_up else -100
        if self.event_bus:
            self.event_bus.emit('character.death', self)

    def update_death(self, dt):
        self.death_vy += self.death_gravity * dt
        self.rect.y += int(self.death_vy * dt)
        return (self._cfg is not None) and (self.rect.top > self._cfg.screen.height + 60)

    # ------------------------------------------------------------------
    # Возрождение
    # ------------------------------------------------------------------

    def spawn_copy(self):
        return self