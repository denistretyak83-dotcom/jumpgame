"""ФР-3: автотайлинг — варианты по маске соседей."""

import importlib.util

import pytest


def _have_pygame() -> bool:
    return importlib.util.find_spec("pygame") is not None


@pytest.fixture
def autotiler():
    if not _have_pygame():
        pytest.skip("pygame недоступен")
    import pygame
    from views.tiles.autotile import AutoTiler

    # простая фабрика: сплошная плашка
    def factory(w, h):
        surf = pygame.Surface((w, h))
        surf.fill((100, 100, 100))
        return surf

    return AutoTiler(factory, 32, 32)


def test_autotiler_returns_surface(autotiler):
    from views.tiles.autotile import AutoTiler

    v = autotiler.variant_for_mask(0)
    assert v.get_size() == (32, 32)


def test_autotiler_all_masks_cached(autotiler):
    # запрос всех 16 масок — возвращает поверхности, кэш заполняется
    from views.tiles.autotile import AutoTiler

    for mask in range(16):
        surf = autotiler.variant_for_mask(mask)
        assert surf.get_size() == (32, 32)


def test_autotiler_same_mask_same_object(autotiler):
    a = autotiler.variant_for_mask(0)
    b = autotiler.variant_for_mask(0)
    assert a is b  # кэширование


def test_compute_mask():
    from views.tiles.autotile import AutoTiler, TILE_MASK_TOP, TILE_MASK_BOTTOM, TILE_MASK_LEFT, TILE_MASK_RIGHT

    assert AutoTiler.compute_mask(True, False, False, False) == TILE_MASK_TOP
    assert AutoTiler.compute_mask(True, True, True, True) == 15
    assert AutoTiler.compute_mask(False, False, False, False) == 0
    assert AutoTiler.compute_mask(False, True, True, False) == (TILE_MASK_BOTTOM | TILE_MASK_LEFT)


def test_autotiler_uses_base_factory(autotiler):
    # версия с маской 0 обведена со всех сторон
    from views.tiles.autotile import AutoTiler

    v = autotiler.variant_for_mask(0)
    # (проверяем, что поверхность создана — рендер реализаций не проверяем пиксельно)
    assert v is not None