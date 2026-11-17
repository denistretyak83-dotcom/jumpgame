"""coin_icon.py -- единый помощник: пиксельная иконка монеты для HUD (Фаза 10).

Раньше дублировалась в Game и main. Теперь -- одна точка, цвета берёт
из config.colors (с fallback на пиксельные дефолты), чтобы тесты не зависели
от полноты словаря цветов.
"""

import pygame


def make_coin_icon(config):
    """Возвращает Surface 16x16 -- иконку монеты (жёлтая с бликом)."""
    colors = getattr(config, "colors", {})
    edge = colors.get("COIN_ICON", (255, 200, 0))
    hlight = colors.get("COIN_ICON_HILIGHT", (255, 240, 100))
    icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(icon, edge, (8, 8), 7)
    pygame.draw.circle(icon, hlight, (6, 6), 4)
    return icon