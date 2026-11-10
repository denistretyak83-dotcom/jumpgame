"""Тесты ParallaxCamera: parallax-смещения слоёв фона."""
import pytest

from core.camera import ParallaxCamera


def test_initial_state():
    cam = ParallaxCamera(screen_width=800, screen_height=600)
    assert cam.width == 800
    assert cam.height == 600
    assert cam.player_x == 0.0


def test_update_records_player_x():
    cam = ParallaxCamera(800, 600)
    cam.update(250.5)
    assert cam.player_x == 250.5


def test_layer_offset_at_origin_is_zero():
    cam = ParallaxCamera(800, 600)
    cam.update(0)
    assert cam.layer_offset(factor=1.0) == 0


def test_layer_offset_non_zero():
    cam = ParallaxCamera(800, 600)
    cam.update(100)
    # offset = -(100 * 0.5) % 800 = -50 % 800 = 750
    assert cam.layer_offset(factor=0.5) == 750


def test_layer_offset_wraps_around_repeat_width():
    cam = ParallaxCamera(800, 600)
    cam.update(1000)
    # -(1000 * 0.2) % 800 = -200 % 800 = 600
    assert cam.layer_offset(factor=0.2) == 600


def test_layer_offset_with_custom_repeat_width():
    cam = ParallaxCamera(800, 600)
    cam.update(50)
    # repeat_width=200: -(50*1.0) % 200 = 150
    assert cam.layer_offset(factor=1.0, repeat_width=200) == 150


def test_apply_adds_offset_to_x():
    cam = ParallaxCamera(800, 600)
    cam.update(100)
    off = cam.layer_offset(factor=0.5)          # 750
    assert cam.apply(0, factor=0.5) == 0 + off  # 750
    assert cam.apply(10, factor=0.5) == 10 + off


def test_apply_with_custom_repeat_width():
    cam = ParallaxCamera(800, 600)
    cam.update(50)
    off = cam.layer_offset(1.0, repeat_width=200)  # 150
    assert cam.apply(5, factor=1.0, repeat_width=200) == 5 + off