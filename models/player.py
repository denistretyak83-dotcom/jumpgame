import pygame
from core.config import settings as config
from models.base_character import BaseCharacter


class Player(BaseCharacter):
    def __init__(self, x, y, animations, use_config=None, event_bus=None):
        if use_config is None:
            use_config = config
        cfg = use_config
        super().__init__(x, y, cfg.player.width, cfg.player.height,
                         animations=animations, config=cfg, event_bus=event_bus)
        self.current_anim = self.animations.get('idle')

    # ------------------------------------------------------------------
    # Контракт: update (intent идёт от контроллера, не keys!)
    # ------------------------------------------------------------------

    def update(self, dt, ctx, intent=None):
        # --- 1. Смерть (приоритетно) ---
        if self.is_dead:
            if self.current_anim:
                self.current_anim.update()
            self.update_death(dt)
            return

        # --- 2. Намерение пользователя -> скорость по X ---
        left = int(intent.left) if intent else 0
        right = int(intent.right) if intent else 0
        self.vel_x = (right - left) * self._cfg.player.speed

        # Направление взгляда (только когда есть явное направление)
        if (left ^ right) and left:
            self.facing_left = True
        elif (left ^ right) and right:
            self.facing_left = False

        # --- 3. Прыжок (только в момент нажатия) ---
        if intent and intent.jump_pressed and self.on_ground:
            self.vel_y = self._cfg.physics.jump_strength
            self.on_ground = False
            if self.event_bus:
                self.event_bus.emit('player.jump')

        # --- 4. Физика (гравитация + коллизии) ---
        self.apply_physics(dt, ctx.platforms)

        # --- 5. Границы экрана ---
        if self.rect.left < 0:
            self.rect.left = 0
        if hasattr(ctx, 'screen_width') and self.rect.right > ctx.screen_width:
            self.rect.right = ctx.screen_width

        # --- 6. Анимация по состоянию движения ---
        self._update_animation()
        if self.current_anim:
            self.current_anim.update()

    # ------------------------------------------------------------------
    # Контракт: get_render_info
    # ------------------------------------------------------------------

    def get_render_info(self):
        if self.is_dead:
            frame = self._current_frame('idle')
            if frame is not None:
                frame = pygame.transform.flip(frame, False, True)
            return {'frame': frame, 'rect': self.rect, 'y': self.rect.y,
                    'facing_left': self.facing_left, 'is_dead': True}

        frame = self.current_anim.current() if self.current_anim else None
        if self.facing_left and frame is not None:
            if (self.current_anim is self.animations.get('idle')
                    or self.current_anim is self.animations.get('jump')):
                frame = pygame.transform.flip(frame, True, False)

        frame_h = frame.get_height() if frame else 0
        return {'frame': frame, 'rect': self.rect, 'y': self.rect.bottom - frame_h,
                'facing_left': self.facing_left, 'is_dead': False}

    # ------------------------------------------------------------------
    # Логика анимации (специфика игрока)
    # ------------------------------------------------------------------

    def _update_animation(self):
        target = 'idle'

        if not self.on_ground:
            # --- В воздухе ---
            if self.vel_y < 0:
                # Летим вверх (прыжок)
                target = 'jump'
            elif self.vel_x != 0:
                # Падаем, но при этом двигаемся горизонтально
                # → оставляем анимацию бега (сохраняем "опору-по-инерции")
                target = 'run_r' if self.vel_x > 0 else 'run_l'
            else:
                # Чистое вертикальное падение почти на месте
                target = 'idle'
        else:
            # --- На земле ---
            if self.vel_x > 0:
                target = 'run_r'
            elif self.vel_x < 0:
                target = 'run_l'
            else:
                target = 'idle'

        # fallback на 'run' если нет направленных анимаций
        if target not in self.animations and target.startswith('run'):
            target = 'run' if 'run' in self.animations else 'idle'

        self._switch_anim(target)