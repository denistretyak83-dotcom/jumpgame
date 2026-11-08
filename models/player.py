from models.base_character import BaseCharacter
from models.behaviors import FallDeathBehavior
from models.player_state import PlayerStateMachine, IdleState
from models.model_state import ModelVisualData
from core.event_bus import GameEvents


class Player(BaseCharacter):
    def __init__(self, x, y, config=None, event_bus=None):
        cfg = config
        death_behavior = None
        if cfg is not None:
            death_behavior = FallDeathBehavior(
                death_cfg=cfg.death,
                screen_height=cfg.screen.height,
            )
        super().__init__(x, y, cfg.player.width, cfg.player.height,
                         config=cfg, event_bus=event_bus,
                         death_behavior=death_behavior,
                         respawn_behavior=None)

        # ВАЖНО: создаётся ПОСЛЕ super().__init__ (нужны vel_x/on_ground)
        self.state_machine = PlayerStateMachine(IdleState())

    def update(self, dt, ctx, intent=None):
        if self.is_dead:
            self.update_death(dt)
            return

        left = int(intent.left) if intent else 0
        right = int(intent.right) if intent else 0
        self.vel_x = (right - left) * self._cfg.player.speed

        if (left ^ right) and left:
            self.facing_left = True
        elif (left ^ right) and right:
            self.facing_left = False

        if intent and intent.jump_pressed and self.on_ground:
            self.vel_y = self._cfg.physics.jump_strength
            self.on_ground = False
            if self.event_bus:
                self.event_bus.emit(GameEvents.PLAYER_JUMP)

        head_bumped = self.apply_physics(dt, ctx.platforms)
        if head_bumped and self.event_bus:
            self.event_bus.emit(GameEvents.PLAYER_BUMP)

        if self.rect.left < 0:
            self.rect.left = 0
        if hasattr(ctx, 'screen_width') and self.rect.right > ctx.screen_width:
            self.rect.right = ctx.screen_width

        # --- ОБНОВЛЕНИЕ СОСТОЯНИЯ (после физики, чтобы vel_y/on_ground актуальны) ---
        self.state_machine.handle(self, intent, dt)

    def get_visual_data(self) -> ModelVisualData:
        facing = self.facing_left
        if self.vel_x < 0:
            facing = True
        elif self.vel_x > 0:
            facing = False

        return ModelVisualData(
            x=self.rect.x, y=self.rect.y,
            width=self.rect.width, height=self.rect.height,
            vel_x=self.vel_x, vel_y=self.vel_y,
            on_ground=self.on_ground, facing_left=facing, is_dead=self.is_dead,
            anim_hint=self.state_machine.get_anim_key(self),   # ← ключ из состояния
        )