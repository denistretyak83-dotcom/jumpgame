from models.base_character import BaseCharacter
from models.behaviors import CallableRespawnBehavior
from models.model_state import ModelVisualData


class Enemy(BaseCharacter):
    def __init__(self, x, y, left, right, config, enemy_data=None):
        super().__init__(x, y, config.enemy.width, config.enemy.height,
                         config=config,
                         death_behavior=None,
                         respawn_behavior=None)
        # Границы патруля. НЕ используем имена left/right, т.к. Entity
        # теперь имеет properties left/right, делегирующие в pygame.Rect.
        self.bound_left = left
        self.bound_right = right
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = config.enemy.speed
        self.pos_x = float(x)
        self.respawn_behavior = CallableRespawnBehavior(
            lambda: Enemy(self.spawn_x, self.spawn_y,
                          self.bound_left, self.bound_right, self._cfg)
        )

    def update(self, dt, ctx=None, intent=None):
        self.pos_x += self.vel_x * dt
        if self.pos_x < self.bound_left:
            overrun = self.bound_left - self.pos_x
            self.pos_x = self.bound_left + overrun
            self.vel_x = abs(self.vel_x)
        elif self.pos_x + self.rect.width > self.bound_right:
            overrun = (self.pos_x + self.rect.width) - self.bound_right
            self.pos_x = self.bound_right - self.rect.width - overrun
            self.vel_x = -abs(self.vel_x)
        self.rect.x = int(round(self.pos_x))

    def get_visual_data(self) -> ModelVisualData:
        return ModelVisualData(
            x=self.rect.x, y=self.rect.y,
            width=self.rect.width, height=self.rect.height,
            vel_x=self.vel_x, vel_y=self.vel_y,
            on_ground=True, facing_left=self.vel_x < 0,
            is_dead=False, anim_hint='walk',
        )