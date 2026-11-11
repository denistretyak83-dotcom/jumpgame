"""ModelVisualData -- нейтральное представление состояния модели для View.

БЕЗ pygame, БЕЗ View-специфики. Модель отдаёт только факты;
View сама превращает их в CharacterVisualState и выбирает анимацию.
"""
from dataclasses import dataclass


@dataclass
class ModelVisualData:
    x: float
    y: float
    width: float
    height: float
    vel_x: float
    vel_y: float
    on_ground: bool
    facing_left: bool
    is_dead: bool
    anim_hint: str = 'idle'    # ← подсказка базовой анимации (игроку 'idle', врагу 'walk')
    anim_group: str | None = None  # ключ группы внешнего вида
