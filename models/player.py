"""Player model -- единая логика: ввод, физика, коллизии, анимация, звуки."""
import pygame
from core.config import settings as config
from models.base_character import BaseCharacter


class Player(BaseCharacter):
    def __init__(self, x, y, animations, sounds, use_config=None):
        if use_config is None:
            use_config = config
        self._cfg = use_config

        # --- Общие поля через BaseCharacter ---
        rect = pygame.Rect(x, y, self._cfg.player.width, self._cfg.player.height)
        super().__init__(rect, animations)

        # --- Скорость и состояние ---
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_left = False

        # Смерть
        self.death_vy = 0
        self.jumping = False

        self._was_on_ground = False  # Для защиты от "тарахтения" при прыжке вверх

        self.sounds = sounds
        self.current_anim = self.animations['idle']

    # ------------------------------------------------------------------
    # Контракт BaseCharacter: update
    # ------------------------------------------------------------------

    def update(self, dt: float, ctx) -> None:
        """ctx -- контекст; здесь нужны ctx.keys и ctx.platforms."""
        keys = ctx.keys
        platforms = ctx.platforms

        # --- 1. Обработка смерти ---
        if self.is_dead:
            self.current_anim.update()
            self.update_death(dt)
            return

        # --- 2. Проверка опоры (FIX для хождения по воздуху) ---
        support = False
        for p in platforms:
            if self.rect.colliderect(p) and abs(self.vel_y) < 0.1:
                support = True
                break

        if support:
            self.on_ground = True
            if self.vel_y > 0.1:
                self.vel_y = 0
        else:
            self.on_ground = False

        # --- 3. Гравитация ---
        if not self.on_ground:
            self.vel_y += self._cfg.physics.gravity * dt

        if self.vel_y > self._cfg.physics.max_fall:
            self.vel_y = self._cfg.physics.max_fall

        self.rect.y += int(self.vel_y * dt)

        # --- 4. Коллизии по Y ---
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0.5 and self.rect.top < p.top:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True

                elif self.vel_y < -0.5 and self.rect.top < p.bottom:
                    self.rect.top = p.bottom
                    self.vel_y = 0
                    if self.sounds:
                        self.sounds.play_bump()

        # --- 5. Ввод и Движение по X ---
        self.vel_x = 0
        speed = self._cfg.player.speed

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -speed
            self.facing_left = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = speed
            self.facing_left = False

        self.rect.x += int(self.vel_x * dt)

        # Коллизии по X (стены)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vel_x > 0:
                    self.rect.right = p.left
                elif self.vel_x < 0:
                    self.rect.left = p.right

        # Границы экрана
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self._cfg.screen.width:
            self.rect.right = self._cfg.screen.width

        # --- 6. Прыжок ---
        jump_pressed = (keys[pygame.K_SPACE] or keys[pygame.K_w]
                        or keys[pygame.K_UP])
        if jump_pressed and self.on_ground and not self.jumping:
            self.vel_y = self._cfg.physics.jump_strength
            self.on_ground = False
            self.jumping = True
            if self.sounds:
                self.sounds.play_jump()
        elif not jump_pressed:
            self.jumping = False

        # --- 7. Анимация ---
        self._update_animation()
        self.current_anim.update()

    # ------------------------------------------------------------------
    # Контракт BaseCharacter: get_render_info
    # ------------------------------------------------------------------

    def get_render_info(self) -> dict:
        if self.is_dead:
            frame = self._current_frame('idle')
            if frame is not None:
                frame = pygame.transform.flip(frame, False, True)
            return {
                'frame': frame,
                'rect': self.rect,
                'y': self.rect.y,  # смерть рисуется от верха
                'facing_left': self.facing_left,
                'is_dead': True,
            }

        frame = self.current_anim.current()
        if self.facing_left and frame is not None:
            if (self.current_anim is self.animations['idle']
                    or self.current_anim is self.animations['jump']):
                frame = pygame.transform.flip(frame, True, False)

        frame_h = frame.get_height() if frame else 0
        return {
            'frame': frame,
            'rect': self.rect,
            'y': self.rect.bottom - frame_h,  # от низа (как было)
            'facing_left': self.facing_left,
            'is_dead': False,
        }

    # ------------------------------------------------------------------
    # Внутренние методы (физика смерти, анимация)
    # ------------------------------------------------------------------

    def _update_animation(self):
        target_anim = None

        if not self.on_ground:
            if self.vel_y < 0:
                target_anim = self.animations['jump']
            else:
                if self.vel_x > 0:
                    target_anim = self.animations['run_r']
                elif self.vel_x < 0:
                    target_anim = self.animations['run_l']
                else:
                    target_anim = self.animations['idle']
        else:
            if self.vel_x > 0:
                target_anim = self.animations['run_r']
            elif self.vel_x < 0:
                target_anim = self.animations['run_l']
            else:
                target_anim = self.animations['idle']

        if self.current_anim is not target_anim:
            self.current_anim = target_anim
            self.current_anim.reset()

    def die(self):
        self.is_dead = True
        self.death_vy = -20
        if self.sounds:
            self.sounds.play_death()

    def update_death(self, dt):
        GRAVITY_DEATH = 50
        self.death_vy += GRAVITY_DEATH * dt
        self.rect.y += int(self.death_vy)
        return self.rect.top > self._cfg.screen.height + 60