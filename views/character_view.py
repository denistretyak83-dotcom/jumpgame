"""CharacterView -- View-слой для движущихся сущностей (MVC).

Модель отдаёт чистое состояние (CharacterVisualState) -- БЕЗ пикселей.
Этот класс превращает состояние в готовый Surface для Renderer.

ВАЖНО про ассеты:
  - player_run/left и player_run/right -- уже раздельные наборы (обе ориентации)
  - player_idle, player_jump, enemy_walk -- один набор (нужен flip для idle/jump)
"""
from dataclasses import dataclass
import pygame


@dataclass
class CharacterVisualState:
    """Чистое логическое состояние сущности для отрисовки (Model)."""
    rect: pygame.Rect
    facing_left: bool = False
    is_dead: bool = False
    anim_key: str = 'idle'      # 'idle' | 'run' | 'jump' | 'walk'
    y_anchor: str = 'bottom'    # 'bottom' (игрок) | 'top' (враг)


class CharacterView:
    """Превращает CharacterVisualState в (frame, x, y) для Renderer."""

    def __init__(self, animations, is_dead_anim='idle'):
        """
        Args:
            animations: dict анимаций с логическими ключами:
                {'idle': Animation, 'run_left': Animation|None,
                 'run_right': Animation|None, 'jump': Animation|None,
                 'walk': Animation|None}
            is_dead_anim: ключ анимации при смерти (обычно 'idle').
        """
        self.animations = animations
        self.is_dead_anim = is_dead_anim

    def render(self, state: CharacterVisualState):
        anim = self._pick_anim(state)
        if anim is None:
            return None, state.rect.x, state.rect.y

        frame = anim.current()
        if frame is None:
            return None, state.rect.x, state.rect.y

        if state.is_dead:
            frame = pygame.transform.flip(frame, False, True)
        else:
            # idle: flip по facing_left
            if state.anim_key == 'idle' and state.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            # jump (направленный, кадр 2): flip по facing_left
            elif state.anim_key == 'jump' and state.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            # jump_neutral (на месте, кадр 1): НЕ флипаем -- нейтральный
            # run_left/run_right/walk: уже повёрнуты ассетами

        if state.y_anchor == 'bottom':
            y = state.rect.bottom - frame.get_height()
        else:
            y = state.rect.y

        return frame, state.rect.x, y

    # ------------------------------------------------------------------
    # Выбор анимации по состоянию
    # ------------------------------------------------------------------

    def _pick_anim(self, state):
        """Выбирает нужную Animation по логическому ключу + направлению."""
        if state.is_dead:
            return self.animations.get(self.is_dead_anim)

        key = state.anim_key

        # Направленные run-анимации берутся по facing_left
        if key == 'run':
            left_key = self.animations.get('run_left')
            right_key = self.animations.get('run_right')
            if state.facing_left and left_key is not None:
                return left_key
            if not state.facing_left and right_key is not None:
                return right_key
            # fallback: если нет направленной, берём любую из двух
            return left_key or right_key

        # Остальные (idle/jump/walk) -- прямой ключ
        return self.animations.get(key)