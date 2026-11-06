from abc import ABC, abstractmethod
import pygame
from models.entity import Entity


class BaseCharacter(Entity, ABC):
    """Богатая база: позиция (Entity) + физика + состояние + смерть + анимации."""

    def __init__(self, x, y, width, height, animations=None, config=None,
                 event_bus=None, death_gravity=50):
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

    @abstractmethod
    def update(self, dt, ctx, intent=None):
        ...

    @abstractmethod
    def get_render_info(self):
        ...

    # ------------------------------------------------------------------
    # Общая физика (гравитация + коллизии с платформами)
    # ------------------------------------------------------------------

    def apply_physics(self, dt, platforms):
        if self.is_dead or self._cfg is None:
            return

        # гравитация (px/с)
        if not self.on_ground:
            self.vel_y += self._cfg.physics.gravity * dt
            if self.vel_y > self._cfg.physics.max_fall:
                self.vel_y = self._cfg.physics.max_fall

        # вертикаль + коллизии
        self.rect.y += int(self.vel_y * dt)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0.5 and self.rect.top < p.top:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < -0.5 and self.rect.top < p.bottom:
                    self.rect.top = p.bottom
                    self.vel_y = 0

        # горизонталь + коллизии
        self.rect.x += int(self.vel_x * dt)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0:
                    self.rect.right = p.left
                elif self.vel_x < 0:
                    self.rect.left = p.right

        self._update_grounded(platforms)

    def _update_grounded(self, platforms):
        """Проверка опоры С ПОМОЩЬЮ КАСАНИЯ, а не строгого colliderect.

        ФИКС: pygame.Rect.colliderect() при точном касании (bottom == top)
        возвращает False, из-за чего on_ground сбрасывался каждый кадр.
        Теперь допуск +8px.
        """
        grounded = False
        for p in platforms:
            if (self.rect.bottom >= p.top - 1
                    and self.rect.bottom <= p.top + 8
                    and self.rect.bottom > p.top - 2
                    and self.vel_y >= -0.5):
                # требуется горизонтальное перекрытие
                if self.rect.right > p.left and self.rect.left < p.right:
                    grounded = True
                    break
        self.on_ground = grounded

    # ------------------------------------------------------------------
    # Общая смерть (кинематографичное падение)
    # ------------------------------------------------------------------

    def die(self, launch_up=True):
        """Помечает сущность мёртвой.

        launch_up=True  -- умеренный подброс вверх (кинематографично).
        launch_up=False -- без подброса (смерть от врага, просто падает вниз).
        """
        if self.is_dead:
            return
        self.is_dead = True
        self.death_vy = -400 if launch_up else -100  # лёгкий подброс
        if self.event_bus:
            self.event_bus.emit('character.death', self)

    def update_death(self, dt):
        """Обновляет падение мёртвой сущности. True -- упал за экран.

        Использует усиленную гравитацию смерти (кинестатографично).
        """
        DEATH_GRAVITY = 1200  # усиленная гравитация для смерти
        self.death_vy += DEATH_GRAVITY * dt
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