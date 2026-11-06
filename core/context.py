"""GameContext -- контекст кадра, передаваемый всем сущностям в update(dt, ctx).

Создаётся один раз за кадр в Game и раздаётся сущностям.
Каждая сущность берёт только нужные ей атрибуты (duck typing).
"""
class GameContext:
    def __init__(self, keys, platforms):
        self.keys = keys          # pygame key-pressed tuple
        self.platforms = platforms  # список rect'ов платформ

    # При необходимости контекст легко расширить новыми полями
    # (например, self.mouse, self.time_scale, self.event_bus ...)