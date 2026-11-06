import pygame
from models.base_character import BaseCharacter
from views.character_view import CharacterVisualState


class Player(BaseCharacter):
    def __init__(self, x, y, config=None, event_bus=None):
        cfg = config  # обязательный конфиг (DI) -- без синглтона
        super().__init__(x, y, cfg.player.width, cfg.player.height,
                         config=cfg, event_bus=event_bus)

    # ------------------------------------------------------------------
    # Контракт: update (intent от контроллера)
    # ------------------------------------------------------------------

    def update(self, dt, ctx, intent=None):
        # --- 1. Смерть ---
        if self.is_dead:
            self.update_death(dt)
            return

        # --- 2. intent -> скорость по X ---
        left = int(intent.left) if intent else 0
        right = int(intent.right) if intent else 0
        self.vel_x = (right - left) * self._cfg.player.speed

        if (left ^ right) and left:
            self.facing_left = True
        elif (left ^ right) and right:
            self.facing_left = False

        # --- 3. Прыжок ---
        if intent and intent.jump_pressed and self.on_ground:
            self.vel_y = self._cfg.physics.jump_strength
            self.on_ground = False
            if self.event_bus:
                self.event_bus.emit('player.jump')

        # --- 4. Физика ---
        head_bumped = self.apply_physics(dt, ctx.platforms)
        if head_bumped and self.event_bus:
            self.event_bus.emit('player.bump')

        # --- 5. Границы экрана ---
        if self.rect.left < 0:
            self.rect.left = 0
        if hasattr(ctx, 'screen_width') and self.rect.right > ctx.screen_width:
            self.rect.right = ctx.screen_width

    # ------------------------------------------------------------------
    # Контракт: get_visual_state (чистое состояние, без пикселей)
    # ------------------------------------------------------------------

    def get_visual_state(self) -> CharacterVisualState:
        # Направление взгляда: при движении -- по vel_x,
        # стоя -- сохраняем последнее значение facing_left
        facing = self.facing_left
        if self.vel_x < 0:
            facing = True
        elif self.vel_x > 0:
            facing = False

        if self.is_dead:
            anim_key = 'idle'
        elif not self.on_ground:
            if self.vel_y < 0:
                # Прыжок вверх: направленный ИЛИ на месте
                anim_key = 'jump' if self.vel_x != 0 else 'jump_neutral'
            elif self.vel_x != 0:
                anim_key = 'run'
            else:
                anim_key = 'idle'
        else:
            anim_key = 'run' if self.vel_x != 0 else 'idle'

        return CharacterVisualState(
            rect=self.rect,
            facing_left=facing,
            is_dead=self.is_dead,
            anim_key=anim_key,
            y_anchor='bottom',
        )