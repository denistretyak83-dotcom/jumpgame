"""ФР-5: squash & stretch — деформация кадра по вертикальной скорости."""

import importlib.util

import pytest


def _have_pygame():
    return importlib.util.find_spec("pygame") is not None


@pytest.fixture
def view():
    if not _have_pygame():
        pytest.skip("pygame недоступен")
    import pygame
    from views.character_view import CharacterView

    class _Anim:
        def __init__(self):
            self.frames = [pygame.Surface((40, 50))]

        def current(self):
            return self.frames[0]

    anim = _Anim()
    # все ключи указывают на одну анимацию, чтобы _pick_anim не возвращал None
    cv = CharacterView({
        "idle": anim,
        "run": anim,
        "run_left": anim,
        "run_right": anim,
        "jump": anim,
        "walk": anim,
    })
    return cv


@pytest.fixture
def state_factory():
    from views.character_view import CharacterVisualState
    import pygame

    def make(vel_y=0.0, anim_key="idle"):
        return CharacterVisualState(
            rect=pygame.Rect(0, 0, 40, 50),
            anim_key=anim_key,
            y_anchor="bottom",
            vel_y=vel_y,
        )
    return make


def test_no_deformation_when_grounded(view, state_factory):
    frame = view.render(state_factory(vel_y=0.0))
    assert frame[0].get_size() == (40, 50)


def test_jump_stretch_increases_height(view, state_factory):
    frame, x, y = view.render(state_factory(vel_y=-500.0, anim_key="jump"))
    w, h = frame.get_size()
    assert h > 50      # растянут вверх
    assert w < 40      # сужен по X


def test_fall_squash_decreases_height(view, state_factory):
    frame, x, y = view.render(state_factory(vel_y=500.0))
    w, h = frame.get_size()
    assert h < 50      # сжат по Y
    assert w > 40      # расширен по X


def test_small_velocity_no_change(view, state_factory):
    # маленькая скорость (< порога) -> без деформации
    frame, x, y = view.render(state_factory(vel_y=0.005))
    assert frame.get_size() == (40, 50)