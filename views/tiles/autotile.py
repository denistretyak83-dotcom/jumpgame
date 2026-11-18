"""
views/tiles/autotile.py — автотайлинг по маске соседей (ФР-3).

Классический ретро-подход (NES): вариант плитки определяется битовой
маской того, есть ли такой же тайл по сторонам (верх/низ/лево/право).

AutoTiler работаеt поверх ЛЮБОГО генератора тайла (функции-фабрики),
что сохраняет OCP: не трогаем RetroTiles/TileFactory.
"""

from collections.abc import Callable

import pygame

# Битовые маски соседей
TILE_MASK_TOP = 1
TILE_MASK_BOTTOM = 2
TILE_MASK_LEFT = 4
TILE_MASK_RIGHT = 8


class AutoTiler:
    """Строит набор вариантов тайла (по маске) из генератора-фабрики.

    tile_factory: Callable[[width, height], pygame.Surface] — базовая плашка
                  (например RetroTiles.grass_top). Из неё генерируются
                  вариации по стыкам (рёбра/углы) простым обводом.
    """

    _EDGE_MASK = [TILE_MASK_LEFT, TILE_MASK_RIGHT, TILE_MASK_TOP, TILE_MASK_BOTTOM]

    def __init__(self, tile_factory: Callable[[int, int], pygame.Surface], width: int, height: int):
        self._factory = tile_factory
        self._width = width
        self._height = height
        self._base = tile_factory(width, height)
        # Кэш вариантов по маске (строим лениво).
        self._variants: dict[int, pygame.Surface] = {}

    # ------------------------------------------------------------------
    def variant_for_mask(self, mask: int) -> pygame.Surface:
        """Возвращает тайл для данной маски соседей (0..15)."""
        if mask not in self._variants:
            self._variants[mask] = self._build_variant(mask)
        return self._variants[mask]

    def _build_variant(self, mask: int) -> pygame.Surface:
        """Рендерит вариант: начинает с базовой плашки и рисует «стыковые»
        рёбра только там, где соседа НЕТ (mask бит не выставлен)."""
        surf = self._base.copy()
        # Внутренние стыки: если нет соседа слева — рисуем вертикальную тёмную линию слева
        if not (mask & TILE_MASK_LEFT):
            pygame.draw.rect(surf, (0, 0, 0), (0, 0, 2, self._height))
        if not (mask & TILE_MASK_RIGHT):
            pygame.draw.rect(surf, (0, 0, 0), (self._width - 2, 0, 2, self._height))
        if not (mask & TILE_MASK_TOP):
            pygame.draw.rect(surf, (0, 0, 0), (0, 0, self._width, 2))
        if not (mask & TILE_MASK_BOTTOM):
            pygame.draw.rect(surf, (0, 0, 0), (0, self._height - 2, self._width, 2))
        return surf

    # ------------------------------------------------------------------
    # Хелпер вычисления маски по соседям
    # ------------------------------------------------------------------
    @staticmethod
    def compute_mask(has_top, has_bottom, has_left, has_right) -> int:
        """Собирает маску из 4 булевых значений наличия соседей."""
        mask = 0
        if has_top:
            mask |= TILE_MASK_TOP
        if has_bottom:
            mask |= TILE_MASK_BOTTOM
        if has_left:
            mask |= TILE_MASK_LEFT
        if has_right:
            mask |= TILE_MASK_RIGHT
        return mask
