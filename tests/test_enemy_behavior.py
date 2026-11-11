"""Тесты EnemyBehavior: реестр (OCP) и поведения walker/chaser/flyer/jumper."""
import pytest

from core.geometry import RectPosition
from models.enemy_behavior import (
    DEFAULT_BEHAVIOR_REGISTRY,
    EnemyBehaviorRegistry,
    WalkerBehavior,
    ChaserBehavior,
    FlyerBehavior,
    JumperBehavior,
)


class FakeEnemy:
    """Минимальный враг, достаточный для поведения."""

    def __init__(self, x=0, y=0, w=32, h=48, speed=10.0,
                 bound_left=0, bound_right=300):
        self.rect = RectPosition(int(x), int(y), int(w), int(h))
        self.width = int(w)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = speed
        self.bound_left = bound_left
        self.bound_right = bound_right


# --------------------------------------------------------------------------
# EnemyBehaviorRegistry
# --------------------------------------------------------------------------
def test_registry_default_is_walker():
    reg = EnemyBehaviorRegistry()
    with pytest.raises(KeyError):
        reg.create("missing")  # у пустого реестра нет даже fallback


def test_registry_register_and_create():
    reg = EnemyBehaviorRegistry()
    reg.register("walker", WalkerBehavior)
    reg.register("chaser", ChaserBehavior)
    assert isinstance(reg.create("walker"), WalkerBehavior)
    assert isinstance(reg.create("chaser"), ChaserBehavior)


def test_default_registry_has_three_behaviors():
    assert isinstance(DEFAULT_BEHAVIOR_REGISTRY.create("walker"), WalkerBehavior)
    assert isinstance(DEFAULT_BEHAVIOR_REGISTRY.create("chaser"), ChaserBehavior)
    assert isinstance(DEFAULT_BEHAVIOR_REGISTRY.create("flyer"), FlyerBehavior)


def test_default_registry_has_jumper():
    assert isinstance(DEFAULT_BEHAVIOR_REGISTRY.create("jumper"), JumperBehavior)


def test_default_registry_fallback_on_unknown():
    behavior = DEFAULT_BEHAVIOR_REGISTRY.create("unknown_type")
    assert isinstance(behavior, WalkerBehavior)


# --------------------------------------------------------------------------
# WalkerBehavior
# --------------------------------------------------------------------------
def test_walker_moves_forward():
    e = FakeEnemy(x=0, bound_right=300, speed=10.0)
    b = WalkerBehavior()
    b.attach(e)
    b.update(e, dt=1.0)
    assert e.pos_x == 10.0


def test_walker_turns_at_left_bound():
    e = FakeEnemy(x=10, bound_left=0, bound_right=300, speed=-50.0)
    b = WalkerBehavior()
    b.attach(e)
    b.update(e, dt=1.0)
    assert e.pos_x == 40.0
    assert e.vel_x > 0
    assert e.pos_x >= e.bound_left


def test_walker_turns_at_right_bound():
    e = FakeEnemy(x=290, w=32, bound_right=300, speed=50.0)
    b = WalkerBehavior()
    b.attach(e)
    b.update(e, dt=1.0)
    assert e.pos_x + e.width <= e.bound_right
    assert e.vel_x < 0


# --------------------------------------------------------------------------
# ChaserBehavior
# --------------------------------------------------------------------------
class Ctx:
    def __init__(self, player_x):
        self.player_x = player_x


def test_chaser_moves_toward_player_from_left():
    e = FakeEnemy(x=0, bound_right=300, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=Ctx(player_x=100))
    assert e.pos_x == 10.0


def test_chaser_moves_toward_player_from_right():
    e = FakeEnemy(x=200, bound_left=0, bound_right=300, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=Ctx(player_x=100))
    assert e.pos_x < 200


def test_chaser_does_not_exit_bounds():
    e = FakeEnemy(x=200, bound_left=0, bound_right=100, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=Ctx(player_x=50))
    assert e.pos_x >= e.bound_left
    assert e.pos_x + e.width <= e.bound_right


def test_chaser_falls_back_to_walker_without_ctx():
    e = FakeEnemy(x=0, bound_right=300, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=None)
    assert e.pos_x == 10.0


# --------------------------------------------------------------------------
# FlyerBehavior
# --------------------------------------------------------------------------
def test_flyer_moves_x_and_oscillates_y():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = FlyerBehavior(amplitude=30, frequency=1.0)
    b.attach(e)
    b.update(e, dt=0.25)
    assert e.pos_x == pytest.approx(2.5)
    assert -30 <= (e.pos_y - 100) <= 30


def test_flyer_syncs_rect_position():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = FlyerBehavior(amplitude=30, frequency=1.0)
    b.attach(e)
    b.update(e, dt=0.25)
    assert e.rect.x == int(round(e.pos_x))
    assert e.rect.y == int(round(e.pos_y))


# --------------------------------------------------------------------------
# JumperBehavior
# --------------------------------------------------------------------------
def test_jumper_patrols_x_within_bounds():
    e = FakeEnemy(x=290, w=32, y=100, bound_right=300, speed=50.0)
    b = JumperBehavior(jump_height=30, jump_interval=1.0)
    b.attach(e)
    b.update(e, dt=0.1)
    assert e.pos_x + e.width <= e.bound_right
    assert e.pos_x >= e.bound_left


def test_jumper_jumps_along_y():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = JumperBehavior(jump_height=30, jump_interval=1.0)
    b.attach(e)
    b.update(e, dt=0.5)
    assert e.pos_y < 100
    assert (100 - e.pos_y) <= 30.0


def test_jumper_returns_to_base_y():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = JumperBehavior(jump_height=30, jump_interval=1.0)
    b.attach(e)
    b.update(e, dt=1.0)
    assert e.pos_y == pytest.approx(100.0)


def test_jumper_syncs_rect_position():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = JumperBehavior(jump_height=30, jump_interval=1.0)
    b.attach(e)
    b.update(e, dt=0.25)
    assert e.rect.x == int(round(e.pos_x))
    assert e.rect.y == int(round(e.pos_y))