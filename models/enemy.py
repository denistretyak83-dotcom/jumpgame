import pygame
from models.base_character import BaseCharacter


class Enemy(BaseCharacter):
    def __init__(self, x, y, left, right, animations, config):
        super().__init__(x, y, config.enemy.width, config.enemy.height,
                         animations=animations, config=config)
        self.left = left
        self.right = right
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = config.enemy.speed   # начальная скорость (вправо)
        self.current_anim = self.animations.get('walk')

    # ------------------------------------------------------------------
    # Контракт: update (патрульный AI)
    # ------------------------------------------------------------------

    def update(self, dt, ctx, intent=None):
        """Патрульный AI. ctx/intent не нужны врагу — сигнатура едина."""
        self.rect.x += int(self.vel_x * dt)

        # Разворот на границах патруля
        if self.rect.left < self.left:
            self.rect.left = self.left
            self.vel_x = abs(self.vel_x)      # идти вправо
        elif self.rect.right > self.right:
            self.rect.right = self.right
            self.vel_x = -abs(self.vel_x)     # идти влево

        if self.current_anim:
            self.current_anim.update()

    # ------------------------------------------------------------------
    # Контракт: get_render_info
    # ------------------------------------------------------------------

    def get_render_info(self):
        return {'frame': self._current_frame('walk'), 'rect': self.rect,
                'y': self.rect.y, 'facing_left': self.vel_x < 0,
                'is_dead': self.is_dead}

    # ------------------------------------------------------------------
    # Возрождение
    # ------------------------------------------------------------------

    def spawn_copy(self):
        """Возвращает копию врага с ИСХОДНЫМИ координатами спавна.

        🔧 ИСПРАВЛЕНО: было self.config (не существует) → теперь self._cfg.
        """
        return Enemy(self.spawn_x, self.spawn_y, self.left, self.right,
                     self.animations, self._cfg)