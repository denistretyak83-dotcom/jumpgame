"""Enemy model -- patrol AI. Наследует BaseCharacter (полиморфизм)."""
import pygame
from models.base_character import BaseCharacter


class Enemy(BaseCharacter):
    def __init__(self, x, y, left, right, animations, config):
        # --- Общие поля через BaseCharacter ---
        rect = pygame.Rect(x, y, config.enemy.width, config.enemy.height)
        super().__init__(rect, animations)

        # --- Патруль ---
        self.left = left
        self.right = right

        # --- Сохраняем всё для spawn_copy (возрождение) ---
        self.config = config
        self.spawn_x = x
        self.spawn_y = y

        # --- Логика движения ---
        self.vel_x = config.enemy.speed
        self.current_anim = self.animations.get('walk')  # None, если нет

    # ------------------------------------------------------------------
    # Контракт BaseCharacter
    # ------------------------------------------------------------------

    def update(self, dt: float, ctx) -> None:
        """Патрульный AI. ctx не нужен врагу, но сигнатура едина (полиморфизм)."""
        # Движение
        self.rect.x += int(self.vel_x * dt)

        # Разворот на границах патруля
        if self.rect.left < self.left:
            self.rect.left = self.left
            self.vel_x = abs(self.vel_x)      # идти вправо
        elif self.rect.right > self.right:
            self.rect.right = self.right
            self.vel_x = -abs(self.vel_x)     # идти влево

        # Обновление кадра анимации
        if self.current_anim:
            self.current_anim.update()

    def get_render_info(self) -> dict:
        return {
            'frame': self._current_frame('walk'),
            'rect': self.rect,
            'y': self.rect.y,  # от верха (как было)
            'facing_left': self.vel_x < 0,
            'is_dead': self.is_dead,
        }

    # ------------------------------------------------------------------
    # Возрождение
    # ------------------------------------------------------------------

    def spawn_copy(self):
        """Возвращает копию врага с ИСХОДНЫМИ координатами спавна."""
        return Enemy(
            x=self.spawn_x,
            y=self.spawn_y,
            left=self.left,
            right=self.right,
            animations=self.animations,
            config=self.config,
        )