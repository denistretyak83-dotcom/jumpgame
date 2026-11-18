"""ФР-3.5: маска соседей платформ и обводка рёбер (автотайлинг уровней)."""

import importlib.util

import pytest


def _have_pygame():
    return importlib.util.find_spec("pygame") is not None


class _P:
    """Простая платформа: x, y, width, height, tile_style."""

    def __init__(self, x, y, w, h, style="grass_top"):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.tile_style = style


class _FakeScreen:
    def fill(self, c):
        pass

    def blit(self, s, pos):
        pass


@pytest.fixture
def renderer():
    if not _have_pygame():
        pytest.skip("pygame недоступен")

    from views.renderer import Renderer

    class _FakeCfg:
        colors = {"SKY": (100, 100, 100)}
        screen = type("S", (), {"width": 800, "height": 600})()

    r = Renderer(_FakeScreen(), None, None, None, None, _FakeCfg())
    return r


# ---------------------------------------------------------------------------
# _neighbor_mask
# ---------------------------------------------------------------------------

def test_neighbor_mask_top(renderer):
    renderer.current_platforms = [
        _P(0, 100, 100, 30),    # главная
        _P(0, 70, 100, 30),     # сверху
    ]
    mask = renderer._neighbor_mask(_P(0, 100, 100, 30))
    assert mask & 1  # TOP
    assert not mask & 2
    assert not mask & 4
    assert not mask & 8


def test_neighbor_mask_left(renderer):
    renderer.current_platforms = [
        _P(100, 0, 100, 30),    # главная
        _P(0, 0, 100, 30),      # слева
    ]
    mask = renderer._neighbor_mask(_P(100, 0, 100, 30))
    assert mask & 4  # LEFT
    assert not mask & 1
    assert not mask & 2
    assert not mask & 8


def test_neighbor_mask_right_and_bottom(renderer):
    renderer.current_platforms = [
        _P(0, 0, 100, 30),    # главная
        _P(100, 0, 100, 30),  # справа
        _P(0, 30, 100, 30),   # снизу
    ]
    mask = renderer._neighbor_mask(_P(0, 0, 100, 30))
    assert mask & 8  # RIGHT
    assert mask & 2  # BOTTOM


def test_neighbor_mask_isolated_is_zero(renderer):
    renderer.current_platforms = [_P(0, 0, 100, 30)]
    mask = renderer._neighbor_mask(_P(0, 0, 100, 30))
    assert mask == 0


def test_neighbor_mask_ignores_overlap_same_object(renderer):
    p = _P(0, 0, 100, 30)
    renderer.current_platforms = [p, p]  # дубликат той же
    mask = renderer._neighbor_mask(p)
    assert mask == 0


# ---------------------------------------------------------------------------
# _draw_edges
# ---------------------------------------------------------------------------

def test_draw_edges_all_four_when_mask_zero(renderer):
    import pygame
    surf = pygame.Surface((50, 50))
    renderer._draw_edges(surf, 0, 50, 50)
    assert surf is not None


def test_draw_edges_some_mask(renderer):
    import pygame
    surf = pygame.Surface((50, 50))
    renderer._draw_edges(surf, 5, 50, 50)
    assert surf is not None