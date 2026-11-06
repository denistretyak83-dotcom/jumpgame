"""GameContext -- контекст кадра, передаваемый всем сущностям в update(dt, ctx).

Создаётся один раз за кадр в Game и раздаётся сущностям.
Каждая сущность берёт только нужные ей атрибуты (duck typing).

Ввод НЕ живёт в контексте — он передаётся отдельно через PlayerIntent
(см. controllers/player_controller.py), чтобы снять зависимость Player
от клавиатуры и pygame.K_*.
"""


class GameContext:
    def __init__(self, platforms, screen_width):
        self.platforms = platforms        # список rect'ов платформ
        self.screen_width = screen_width  # ширина экрана (для границ)

    # Контекст легко расширить новыми полями
    # (например: self.time_scale, self.animations, self.scene...).