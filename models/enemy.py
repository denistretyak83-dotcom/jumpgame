from models.base_character import BaseCharacter
from models.behaviors import CallableRespawnBehavior
from models.enemy_behavior import EnemyBehavior, DEFAULT_BEHAVIOR_REGISTRY
from models.model_state import ModelVisualData


class Enemy(BaseCharacter):
    """Враг: движение управляется поведением (композиция, OCP)."""

    def __init__(self, x, y, left, right, config, enemy_data=None,
                 behavior_registry=None):
        data = enemy_data or {}
        # Поведение — по ключу "behavior", не путать с "type" сущности.
        self.behavior_type = data.get("behavior", "walker")

        super().__init__(x, y, config.enemy.width, config.enemy.height,
                         config=config, death_behavior=None, respawn_behavior=None)

        self.bound_left = left
        self.bound_right = right
        self.spawn_x = x
        self.spawn_y = y
        self.vel_x = config.enemy.speed
        self.pos_x = float(x)
        self.sprite_key = data.get("sprite", "walker")

        self._behavior_registry = behavior_registry or DEFAULT_BEHAVIOR_REGISTRY
        self.behavior: EnemyBehavior = self._behavior_registry.create(
            self.behavior_type)
        self.behavior.attach(self)

        self.respawn_behavior = CallableRespawnBehavior(
            lambda: Enemy(self.spawn_x, self.spawn_y,
                          self.bound_left, self.bound_right,
                          self._cfg, enemy_data=data,
                          behavior_registry=self._behavior_registry)
        )

    def update(self, dt, ctx=None, intent=None):
        """Делегирует ежекадровую логику прикреплённому поведению."""
        self.behavior.update(self, dt, ctx, intent)

    def get_visual_data(self) -> ModelVisualData:
        return ModelVisualData(
            x=self.rect.x, y=self.rect.y,
            width=self.rect.width, height=self.rect.height,
            vel_x=self.vel_x, vel_y=self.vel_y,
            on_ground=True, facing_left=self.vel_x < 0,
            is_dead=False, anim_hint='walk', anim_group=self.sprite_key
        )
