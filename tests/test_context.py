"""Тесты GameContext: контекст кадра с платформами и width."""
import pytest

from core.context import GameContext


def test_context_stores_platforms_and_width():
    platforms = [object(), object()]   # заглушки платформ
    ctx = GameContext(platforms, screen_width=800)
    assert ctx.platforms is platforms
    assert ctx.screen_width == 800


def test_context_player_x_defaults_to_zero():
    ctx = GameContext([], 800)
    assert ctx.player_x == 0.0


def test_context_player_x_as_float():
    ctx = GameContext([], 800, player_x=123)
    assert ctx.player_x == 123.0
    assert isinstance(ctx.player_x, float)


def test_context_can_be_extended():
    ctx = GameContext([], 800)
    # duck typing: контекст легко расширять новыми атрибутами
    ctx.time_scale = 1.0
    ctx.scene = "level_1"
    assert ctx.time_scale == 1.0
    assert ctx.scene == "level_1"