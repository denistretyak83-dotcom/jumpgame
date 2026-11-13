"""Тесты рефакторинга Renderer.draw: fat-interface -> RenderState (шаг 5).

Внешние отрисовки (фон, HUD, fade, платформы) мокаются, чтобы проверить
логику draw с одним аргументом RenderState без реального pygame-рендера.
"""

import unittest.mock

import pytest

from views.renderer import Renderer
from views.render_state import RenderState


class _ShortFont:
    def render(self, text, antialias, color):
        return object()


class _FakeConfig:
    colors = {
        "SKY": (100, 100, 100),
        "BROWN": (80, 40, 0),
        "ORANGE": (255, 150, 0),
        "RED": (255, 0, 0),
        "BLACK": (0, 0, 0),
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


@pytest.fixture
def renderer():
    r = Renderer(
        screen=_FakeScreen(),
        sprite_cache=None,
        coin_icon=None,
        font=_ShortFont(),
        small_font=_ShortFont(),
        config=_FakeConfig(),
    )
    # Отключаем реальные отрисовки фона/HUD/fade (тестируем только draw-логику).
    r.background = unittest.mock.MagicMock()
    return r


@pytest.fixture
def base_state():
    return RenderState(
        entities=[], coins=[], coin_collected=[], flag_rect=None,
        score=0, lives=3, seconds=0.0, state_manager=None,
        won=False, game_over=False, fade_level=0, camera=_FakeCamera(),
    )


def test_renderer_draw_accepts_render_state(renderer, base_state):
    with unittest.mock.patch("views.renderer.draw_retro_hud"):
        renderer.draw(base_state)  # smoke: без исключений


def test_renderer_draw_shows_win_text_when_won(renderer, base_state):
    base_state.won = True
    with unittest.mock.patch("views.renderer.draw_retro_hud"):
        renderer.draw(base_state)  # ветка "YOU WIN!" через фейковый шрифт


def test_renderer_draw_game_over_uses_fade(renderer, base_state):
    base_state.game_over = True
    base_state.fade_level = 300  # >=180: только пиксельный фейд, без текста
    with unittest.mock.patch("views.renderer.draw_retro_hud"), \
         unittest.mock.patch("views.renderer.draw_pixelated_fade") as fade:
        renderer.draw(base_state)
    fade.assert_called_once()


def test_renderer_draw_with_coins(renderer, base_state):
    class _Coin:
        def to_pygame_rect(self):
            return unittest.mock.MagicMock()  # с inflate(...)

    base_state.coins = [_Coin()]
    base_state.coin_collected = [False]
    with unittest.mock.patch("views.renderer.draw_retro_hud"), \
         unittest.mock.patch("pygame.draw.ellipse"):
        renderer.draw(base_state)  # штриховка монеты повторно по inflate(...)