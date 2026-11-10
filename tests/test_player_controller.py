"""Тесты PlayerController: преобразование клавиш в PlayerIntent (ввод)."""
import importlib.util
from collections import defaultdict

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None
import pygame  # noqa: E402

from controllers.player_controller import PlayerController, PlayerIntent  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужны константы K_*)"
)


def make_empty_keys():
    """Заглушка pygame.key.get_pressed(): отсутствующий ключ -> False."""
    return defaultdict(bool)


def test_intent_defaults():
    intent = PlayerIntent()
    assert intent.left is False
    assert intent.right is False
    assert intent.jump is False
    assert intent.jump_pressed is False


def test_handle_input_no_keys_returns_empty_intent():
    ctrl = PlayerController()
    intent = ctrl.handle_input(make_empty_keys())
    assert intent.left is False
    assert intent.right is False
    assert intent.jump is False
    assert intent.jump_pressed is False


def test_handle_input_left_key():
    ctrl = PlayerController()
    keys = make_empty_keys()
    keys[pygame.K_LEFT] = True
    intent = ctrl.handle_input(keys)
    assert intent.left is True
    assert intent.right is False


def test_handle_input_right_key():
    ctrl = PlayerController()
    keys = make_empty_keys()
    keys[pygame.K_RIGHT] = True
    intent = ctrl.handle_input(keys)
    assert intent.right is True
    assert intent.left is False


def test_handle_input_alternate_keys():
    ctrl = PlayerController(
        jump_keys=(pygame.K_x,),
        left_keys=(pygame.K_1,),
        right_keys=(pygame.K_2,),
    )
    keys = make_empty_keys()
    keys[pygame.K_1] = True
    intent = ctrl.handle_input(keys)
    assert intent.left is True
    assert intent.jump is False


def test_jump_held_sets_jump_true_but_edge_false_first():
    ctrl = PlayerController()
    keys = make_empty_keys()
    keys[pygame.K_SPACE] = True
    intent = ctrl.handle_input(keys)
    assert intent.jump is True
    assert intent.jump_pressed is True


def test_jump_held_second_frame_edge_false():
    ctrl = PlayerController()
    keys = make_empty_keys()
    keys[pygame.K_SPACE] = True
    ctrl.handle_input(keys)
    intent2 = ctrl.handle_input(keys)
    assert intent2.jump is True
    assert intent2.jump_pressed is False


def test_jump_release_resets_edge_for_next_press():
    ctrl = PlayerController()
    press = make_empty_keys()
    press[pygame.K_SPACE] = True
    release = make_empty_keys()

    ctrl.handle_input(press)
    ctrl.handle_input(press)
    ctrl.handle_input(release)
    intent = ctrl.handle_input(press)
    assert intent.jump is True
    assert intent.jump_pressed is True


def test_jump_pressed_is_false_when_released():
    ctrl = PlayerController()
    press = make_empty_keys()
    press[pygame.K_SPACE] = True
    release = make_empty_keys()
    ctrl.handle_input(press)
    intent = ctrl.handle_input(release)
    assert intent.jump is False
    assert intent.jump_pressed is False


def test_edge_detection_uses_internal_state_sequential_calls():
    ctrl = PlayerController()
    empty = make_empty_keys()
    ctrl.handle_input(empty)
    press = make_empty_keys()
    press[pygame.K_SPACE] = True
    intent = ctrl.handle_input(press)
    assert intent.jump_pressed is True