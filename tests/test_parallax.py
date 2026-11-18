"""ФР-4: параллакс-фон — разные скорости дают разные смещения, контракт соблюдён."""

import importlib.util

import pytest


def _have_pygame():
    return importlib.util.find_spec("pygame") is not None


@pytest.fixture
def background():
    if not _have_pygame():
        pytest.skip("pygame недоступен")
    from views.backgrounds import RetroBackground

    class _Cfg:
        colors = {"SKY_RETRO": (1, 2, 3), "SKY": (4, 5, 6)}

    return RetroBackground(800, 600, config=_Cfg(), )

def test_background_is_protocol():
    from views.backgrounds import Background
    from views.backgrounds import RetroBackground
    b = RetroBackground(800, 600)
    assert isinstance(b, Background) is True


def test_layer_offsets_differ_for_different_speeds():
    from views.backgrounds import RetroBackground
    b = RetroBackground(800, 600)
    b.update(100)
    off_slow = b.camera.layer_offset(0.05, 800)
    off_fast = b.camera.layer_offset(0.15, 800)
    # разные скорости -> разные смещения
    assert off_slow != off_fast


def test_background_has_layers():
    from views.backgrounds import RetroBackground
    b = RetroBackground(800, 600)
    assert len(b.layers) == 3


def test_draw_does_not_crash():
    import pygame
    if not _have_pygame():
        pytest.skip("pygame недоступен")
    from views.backgrounds import RetroBackground
    b = RetroBackground(800, 600)
    screen = pygame.Surface((800, 600))
    b.draw(screen, 100)

def test_layer_offset_zero_factor_is_zero():
    from views.backgrounds import RetroBackground
    b = RetroBackground(800, 600)
    b.update(100)
    assert b.camera.layer_offset(0, 800) == 0


def test_layer_offset_wraps_in_range():
    from views.backgrounds import RetroBackground
    b = RetroBackground(800, 600)
    b.update(10)  # смещение в пределах диапазона
    off = b.camera.layer_offset(0.5, 800)
    assert 0 <= off < 800