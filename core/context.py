"""GameContext -- контекст кадра, передаваемый всем сущностям в update(dt, ctx).

Создаётся один раз за кадр в Game и раздаётся сущностям.
Каждая сущность берёт только нужные ей атрибуты (duck typing).

Ввод НЕ живёт в контексте — он передаётся отдельно через PlayerIntent
(см. controllers/player_controller.py), чтобы снять зависимость Player
от клавиатуры и pygame.K_*.
"""


class GameContext:
    def __init__(self, platforms, screen_width, player_x=0.0):
        self.platforms = platforms
        self.screen_width = screen_width
        self.player_x = float(player_x)  # позиция игрока (для поведения chaser)

    # Контекст легко расширить новыми полями
    # (например: self.time_scale, self.animations, self.scene...).
