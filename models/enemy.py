from models.base_character import BaseCharacter
from models.behaviors import CallableRespawnBehavior
from views.character_view import CharacterVisualState


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

        # --- DI: компонент возрождения через фабрику (без циклического импорта) ---
        self.respawn_behavior = CallableRespawnBehavior(
            lambda: Enemy(self.spawn_x, self.spawn_y,
                          self.left, self.right, self._cfg)
        )

    def update(self, dt, ctx=None, intent=None):
        self.rect.x += int(self.vel_x * dt)

        if self.rect.left < self.left:
            self.rect.left = self.left
            self.vel_x = abs(self.vel_x)
        elif self.rect.right > self.right:
            self.rect.right = self.right
            self.vel_x = -abs(self.vel_x)

    def get_visual_state(self) -> CharacterVisualState:
        return CharacterVisualState(
            rect=self.rect,
            facing_left=self.vel_x < 0,
            is_dead=self.is_dead,
            anim_key='walk',
            y_anchor='top',      # враг рисуется от верха
        )