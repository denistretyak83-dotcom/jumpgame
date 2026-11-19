"""CharacterView -- View-слой для движущихся сущностей (MVC).

Модель отдаёт чистое состояние (CharacterVisualState) -- БЕЗ пикселей.
Этот класс превращает состояние в готовый Surface для Renderer.

ВАЖНО про ассеты:
  - player_run/left и player_run/right -- уже раздельные наборы (обе ориентации)
  - player_idle, player_jump, enemy_walk -- один набор (нужен flip для idle/jump)

ФР-5 (squash & stretch): CharacterVisualState несёт vel_y из модели, а render
деформирует кадр в классическом мультяшном стиле (Sonic/Mario):
  - прыжок вверх (vel_y < 0):  растяжение по Y, сужение по X;
  - падение (vel_y > 0):       сжатие по Y, расширение по X;
  - на земле / нет скорости:   без деформации.
"""

from dataclasses import dataclass

import pygame

from models.model_state import ModelVisualData


@dataclass
class CharacterVisualState:
    """Чистое логическое состояние сущности для отрисовки (Model)."""

    rect: pygame.Rect
    facing_left: bool = False
    is_dead: bool = False
    anim_key: str = "idle"  # 'idle' | 'run' | 'jump' | 'walk'
    y_anchor: str = "bottom"  # 'bottom' (игрок) | 'top' (враг)
    vel_y: float = 0.0  # ФР-5: вертикальная скорость (для squash&stretch)

    # Пороги деформации (можно настраивать)
    JUMP_STRETCH = (0.9, 1.2)  # (scale_x, scale_y) при прыжке вверх
    FALL_SQUASH = (1.15, 0.85)  # (scale_x, scale_y) при падении


class CharacterView:
    """Превращает CharacterVisualState в (frame, x, y) для Renderer."""

    def __init__(self, animations, is_dead_anim="idle"):
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

    # ---------- маппер фактов модели -> DTO View ----------
    def build_state(self, data: ModelVisualData, y_anchor="bottom") -> CharacterVisualState:
        """Строит CharacterVisualState из чистых фактов модели."""
        return CharacterVisualState(
            rect=pygame.Rect(data.x, data.y, data.width, data.height),
            facing_left=data.facing_left,
            is_dead=data.is_dead,
            anim_key=self.resolve_anim(data),
            y_anchor=y_anchor,
            vel_y=data.vel_y,  # ФР-5
        )

    def resolve_anim(self, data: ModelVisualData) -> str:
        if data.is_dead:
            return self.is_dead_anim
        return data.anim_hint

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
            if (
                state.anim_key == "idle"
                and state.facing_left
                or state.anim_key == "jump"
                and state.facing_left
            ):
                frame = pygame.transform.flip(frame, True, False)

        # ФР-5: squash & stretch в зависимости от вертикальной скорости
        frame = self._apply_squash(frame, state)

        y = state.rect.bottom - frame.get_height() if state.y_anchor == "bottom" else state.rect.y
        return frame, state.rect.x, y

    # ------------------------------------------------------------------
    # ФР-5: деформация кадра (squash & stretch)
    # ------------------------------------------------------------------
    def _apply_squash(self, frame, state) -> pygame.Surface:
        """Возвращает кадр, деформированный по вертикальной скорости."""
        if state.is_dead or abs(state.vel_y) < 0.01:
            return frame  # без деформации на земле/мёртвом

        w, h = frame.get_size()
        if state.vel_y < 0:
            sx, sy = CharacterVisualState.JUMP_STRETCH
        else:
            sx, sy = CharacterVisualState.FALL_SQUASH

        new_w = max(1, int(w * sx))
        new_h = max(1, int(h * sy))
        if (new_w, new_h) == (w, h):
            return frame
        return pygame.transform.scale(frame, (new_w, new_h))

    # ------------------------------------------------------------------
    # Выбор анимации по состоянию
    # ------------------------------------------------------------------
    def _pick_anim(self, state):
        if state.is_dead:
            return self.animations.get(self.is_dead_anim)
        key = state.anim_key
        if key == "run":
            left_key = self.animations.get("run_left")
            right_key = self.animations.get("run_right")
            if state.facing_left and left_key is not None:
                return left_key
            if not state.facing_left and right_key is not None:
                return right_key
            return left_key or right_key
        return self.animations.get(key)
