"""Тесты PlayerStateMachine: переходы Idle/Run/Jump/Fall и get_anim_key."""
import pytest

from models.player_state import (
    PlayerStateMachine,
    IdleState,
    RunState,
    JumpState,
    FallState,
)


class FakePlayer:
    def __init__(self, on_ground=True, vel_x=0.0, vel_y=0.0):
        self.on_ground = on_ground
        self.vel_x = vel_x
        self.vel_y = vel_y


class Intent:
    def __init__(self, left=0, right=0, jump_pressed=False):
        self.left = left
        self.right = right
        self.jump_pressed = jump_pressed


# --------------------------------------------------------------------------
# начальное состояние / get_anim_key
# --------------------------------------------------------------------------
def test_default_state_is_idle():
    sm = PlayerStateMachine()
    assert isinstance(sm.state, IdleState)


def test_idle_anim_key():
    sm = PlayerStateMachine(IdleState())
    p = FakePlayer()
    assert sm.get_anim_key(p) == 'idle'


def test_start_with_jump_state_anim():
    sm = PlayerStateMachine(JumpState())
    p = FakePlayer(vel_x=0.0)
    assert sm.get_anim_key(p) == 'jump_neutral'   # vel_x==0 -> neutral
    p2 = FakePlayer(vel_x=5.0)
    assert sm.get_anim_key(p2) == 'jump'          # vel_x!=0 -> jump


# --------------------------------------------------------------------------
# Idle -> переходы
# --------------------------------------------------------------------------
def test_idle_stays_idle_on_ground_no_intent():
    sm = PlayerStateMachine(IdleState())
    p = FakePlayer(on_ground=True, vel_x=0.0)
    sm.handle(p, None, 0.1)
    assert isinstance(sm.state, IdleState)


def test_idle_to_run_when_moving():
    sm = PlayerStateMachine(IdleState())
    p = FakePlayer(on_ground=True, vel_x=5.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, RunState)


def test_idle_to_jump_when_jump_pressed():
    sm = PlayerStateMachine(IdleState())
    p = FakePlayer(on_ground=True, vel_x=0.0)
    sm.handle(p, Intent(jump_pressed=True), 0.1)
    assert isinstance(sm.state, JumpState)


def test_idle_to_fall_when_not_ground_and_falling():
    sm = PlayerStateMachine(IdleState())
    p = FakePlayer(on_ground=False, vel_y=5.0)  # падает
    sm.handle(p, None, 0.1)
    assert isinstance(sm.state, FallState)


def test_idle_to_jump_when_not_ground_and_rising():
    sm = PlayerStateMachine(IdleState())
    p = FakePlayer(on_ground=False, vel_y=-5.0)  # летит вверх
    sm.handle(p, None, 0.1)
    assert isinstance(sm.state, JumpState)


# --------------------------------------------------------------------------
# Run -> переходы
# --------------------------------------------------------------------------
def test_run_stays_run_when_moving():
    sm = PlayerStateMachine(RunState())
    p = FakePlayer(on_ground=True, vel_x=5.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, RunState)


def test_run_to_idle_when_stopped():
    sm = PlayerStateMachine(RunState())
    p = FakePlayer(on_ground=True, vel_x=0.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, IdleState)


def test_run_to_jump_when_jump_pressed():
    sm = PlayerStateMachine(RunState())
    p = FakePlayer(on_ground=True, vel_x=5.0)
    sm.handle(p, Intent(jump_pressed=True), 0.1)
    assert isinstance(sm.state, JumpState)


def test_run_to_fall_when_off_ground_falling():
    sm = PlayerStateMachine(RunState())
    p = FakePlayer(on_ground=False, vel_y=3.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, FallState)


# --------------------------------------------------------------------------
# Jump -> Fall
# --------------------------------------------------------------------------
def test_jump_to_fall_when_vel_y_non_negative():
    sm = PlayerStateMachine(JumpState())
    p = FakePlayer(on_ground=False, vel_y=5.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, FallState)


def test_jump_stays_jump_while_rising():
    sm = PlayerStateMachine(JumpState())
    p = FakePlayer(on_ground=False, vel_y=-5.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, JumpState)


# --------------------------------------------------------------------------
# Fall -> обратно на землю / прыжок
# --------------------------------------------------------------------------
def test_fall_to_idle_when_landed_and_stopped():
    sm = PlayerStateMachine(FallState())
    p = FakePlayer(on_ground=True, vel_x=0.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, IdleState)


def test_fall_to_run_when_landed_and_moving():
    sm = PlayerStateMachine(FallState())
    p = FakePlayer(on_ground=True, vel_x=3.0)
    sm.handle(p, Intent(), 0.1)
    assert isinstance(sm.state, RunState)


def test_fall_anim_key_neutral_vs_run():
    sm = PlayerStateMachine(FallState())
    p = FakePlayer(vel_x=0.0)
    assert sm.get_anim_key(p) == 'idle'
    p2 = FakePlayer(vel_x=4.0)
    assert sm.get_anim_key(p2) == 'run'