from abc import ABC, abstractmethod
import pygame
from models.entity import Entity
from models.physics import PhysicsComponent, PhysicsConfig


class BaseCharacter(Entity, ABC):
    """Лёгкая база: состояние + игровой контракт.

    Физика делегируется PhysicsComponent (композиция).
    Смерть и анимации -- ответственности, которые наследники
    используют по необходимости.
    """

    def __init__(self, x, y, width, height, animations=None, config=None,
                 event_bus=None, death_gravity=1200):
        super().__init__(x, y, width, height)
        self.animations = animations if animations else {}
        self.current_anim = self._first_anim()
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
    def get_render_info(self):
        ...

    # ------------------------------------------------------------------
    # Физика теперь ЧЕРЕЗ компонент (доступ для наследников)
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
        # при смерти обнуляем горизонтальную физику
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

    # ------------------------------------------------------------------
    # Анимация (хелперы)
    # ------------------------------------------------------------------

    def _current_frame(self, anim_key):
        anim = self.animations.get(anim_key)
        return anim.current() if anim else None

    def _switch_anim(self, key):
        anim = self.animations.get(key)
        if anim is None or anim is self.current_anim:
            return False
        self.current_anim = anim
        self.current_anim.reset()
        return True

    def _first_anim(self):
        for anim in self.animations.values():
            return anim
        return None