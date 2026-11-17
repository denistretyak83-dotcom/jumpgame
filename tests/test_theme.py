"""Фаза 10: цвета монет/иконки централизованы в config (тема).

Проверяем, что Renderer берёт цвета монет из config.colors с fallback,
а make_coin_icon читает ключи COIN_ICON из конфига.
"""

import unittest.mock

import pygame
import pytest

from views.coin_icon import make_coin_icon


class _FakeConfig:
    colors = {
        "SKY": (100, 100, 100),
        "BROWN": (80, 40, 0),
        "ORANGE": (255, 150, 0),
        "RED": (255, 0, 0),
        "BLACK": (0, 0, 0),
        "COIN_EDGE": (11, 22, 33),
        "COIN": (44, 55, 66),
        "COIN_HILIGHT": (77, 88, 99),
    }
    screen = type("S", (), {"width": 800, "height": 600})()
    assets = type("A", (), {"font_size": 24, "small_font_size": 12})()


class _FakeScreen:
    def fill(self, color):
        pass

    def blit(self, surface, pos):
        pass


class _FakeCamera:
    player_x = 100.0


class _FakeCoin:
    def to_pygame_rect(self):
        return pygame.Rect(10, 10, 20, 20)


def _make_renderer():
    from views.renderer import Renderer

    font = type("F", (), {"render": lambda self, a, b, c: object()})()
    r = Renderer(
        screen=_FakeScreen(),
        sprite_cache=None,
        coin_icon=None,
        font=font,
        small_font=font,
        config=_FakeConfig(),
    )
    r.background = unittest.mock.MagicMock()
    return r


def test_renderer_uses_theme_coin_colors():
    from views.render_state import RenderState

    renderer = _make_renderer()
    state = RenderState(
        entities=[], coins=[_FakeCoin()], coin_collected=[False], flag_rect=None,
        score=0, lives=3, seconds=0.0, state_manager=None,
        won=False, game_over=False, fade_level=0, camera=_FakeCamera(),
    )
    captured = []
    with unittest.mock.patch("views.renderer.draw_retro_hud"):
        with unittest.mock.patch("pygame.draw.ellipse") as ellipse:
            renderer.draw(state)
            for call in ellipse.call_args_list:
                captured.append(call.args[1])

    # монета рисуется тремя эллипсами: EDGE, COIN, COIN_HILIGHT (из конфига)
    assert (11, 22, 33) in captured   # COIN_EDGE
    assert (44, 55, 66) in captured   # COIN
    assert (77, 88, 99) in captured   # COIN_HILIGHT


def test_color_fallback_when_missing():
    """Конфиг без COIN-ключей (как в старых тестах) не ломает рендер."""
    from views.renderer import Renderer

    cfg = _FakeConfig()
    # убираем COIN-ключи -- как в существующем test_renderer
    for k in ("COIN_EDGE", "COIN", "COIN_HILIGHT"):
        cfg.colors.pop(k)

    renderer = _make_renderer()
    from views.render_state import RenderState
    state = RenderState(
        entities=[], coins=[_FakeCoin()], coin_collected=[False], flag_rect=None,
        score=0, lives=3, seconds=0.0, state_manager=None,
        won=False, game_over=False, fade_level=0, camera=_FakeCamera(),
    )
    with unittest.mock.patch("views.renderer.draw_retro_hud"), \
         unittest.mock.patch("pygame.draw.ellipse"):
        renderer.draw(state)  # без KeyError -- дефолты


def test_make_coin_icon_uses_config_colors():
    cfg = _FakeConfig()
    icon = make_coin_icon(cfg)
    assert isinstance(icon, pygame.Surface)
    assert icon.get_size() == (16, 16)