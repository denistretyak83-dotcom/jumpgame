from models.base_character import BaseCharacter
from models.behaviors import CallableRespawnBehavior
from models.model_state import ModelVisualData


class Enemy(BaseCharacter):
    def __init__(self, x, y, left, right, config):
        # --- без death_behavior: у врага смерти в update нет ---
        super().__init__(x, y, config.enemy.width, config.enemy.height,
                         config=config,
                         death_behavior=None,
                         respawn_behavior=None)

        self.left = left
        self.right = right
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = config.enemy.speed

        # float-позиция: точное движение, независимое от дискретизации int()
        self.pos_x = float(x)

        # --- DI: компонент возрождения через фабрику ---
        self.respawn_behavior = CallableRespawnBehavior(
            lambda: Enemy(self.spawn_x, self.spawn_y,
                          self.left, self.right, self._cfg)
        )

    def update(self, dt, ctx=None, intent=None):
        """Движение патруля с FPS-независимыми границами (float-позиция)."""
        # 1. Аккумулируем точное перемещение
        self.pos_x += self.vel_x * dt

        # 2. Отражаем от границ (с учётом ширины спрайта), не теряя остаток
        if self.pos_x < self.left:
            overrun = self.left - self.pos_x          # сколько "перелетели" влево
            self.pos_x = self.left + overrun          # отражаем зеркально внутрь
            self.vel_x = abs(self.vel_x)
        elif self.pos_x + self.rect.width > self.right:
            overrun = (self.pos_x + self.rect.width) - self.right
            self.pos_x = self.right - self.rect.width - overrun
            self.vel_x = -abs(self.vel_x)

        # 3. Синхронизируем pygame.Rect с float-позицией
        self.rect.x = int(round(self.pos_x))

    # models/enemy.py (добавьте ЭТОТ метод в класс Enemy)

    def get_visual_data(self) -> ModelVisualData:
        return ModelVisualData(
            x=self.rect.x, y=self.rect.y,
            width=self.rect.width, height=self.rect.height,
            vel_x=self.vel_x, vel_y=self.vel_y,
            on_ground=True, facing_left=self.vel_x < 0,
            is_dead=False, anim_hint='walk',
        )