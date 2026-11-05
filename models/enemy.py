"""Enemy model -- patrol AI and rendering."""
import pygame


class Enemy:
    def __init__(self, x, y, left, right, animations, config):
        # Инициализация координат
        self.rect = pygame.Rect(x, y, config.enemy.width, config.enemy.height)

        # Сохраняем границы патруля
        self.left = left
        self.right = right

        # --- ИСПРАВЛЕНИЕ: Сохраняем конфиг для spawn_copy ---
        self.config = config

        # --- ИСПРАВЛЕНИЕ: Сохраняем стартовые координаты для возрождения ---
        self.spawn_x = x
        self.spawn_y = y

        # --- АНИМАЦИЯ ---
        self.animations = animations
        # Безопасное получение анимации (защита от None)
        self.current_anim = self.animations.get('walk') if animations else None

        # Логика движения
        self.vel_x = config.enemy.speed

    def update(self, dt):
        # Движение
        self.rect.x += int(self.vel_x * dt)

        # Патрулирование (разворот)
        if self.rect.left < self.left:
            self.rect.left = self.left
            self.vel_x = abs(self.vel_x)  # Идти вправо
        elif self.rect.right > self.right:
            self.rect.right = self.right
            self.vel_x = -abs(self.vel_x)  # Идти влево

        # Обновление кадра анимации
        if self.current_anim:
            self.current_anim.update()

    def spawn_copy(self):
        """Возвращает копию врага, используя ИСХОДНЫЕ координаты спавна."""
        return Enemy(
            x=self.spawn_x,  # Используем сохраненные x
            y=self.spawn_y,  # Используем сохраненные y
            left=self.left,
            right=self.right,
            animations=self.animations,
            config=self.config
        )