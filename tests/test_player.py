"""Тесты Player: конструктор, update (движение/прыжок), visual data."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from models.player import Player  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeCfg:
    class PlayerParams:
        width = 32
        height = 48
        speed = 200.0

    class ScreenParams:
        width = 800
        height = 600

    class DeathParams:
        # FallDeathBehavior параметры; значения подставляем по минимуму
        rise_speed = 300.0
        timer = 1.0

    class PhysicsParams:
        jump_strength = -400.0

    player = PlayerParams()
    screen = ScreenParams()
    death = DeathParams()
    physics = PhysicsParams()


class Intent:
    def __init__(self, left=0, right=0, jump_pressed=False):
        self.left = left
        self.right = right
        self.jump_pressed = jump_pressed


class Ctx:
    def __init__(self, platforms=None, screen_width=800):
        self.platforms = platforms or []
        self.screen_width = screen_width


def make_player(x=0, y=0, cfg=None, event_bus=None):
    return Player(x, y, config=cfg or FakeCfg(), event_bus=event_bus)


def test_player_initial_state():
    p = make_player()
    assert p.is_dead is False
    assert p.on_ground is False
    assert p.vel_x == 0.0
    assert p.state_machine is not None


def test_player_update_moves_right():
    p = make_player()
    # intent right, скорость 200 -> vel_x = (1-0)*200 = 200
    p.update(1.0, Ctx(), Intent(left=0, right=1))
    assert p.vel_x == 200.0

def test_player_update_moves_left():
    p = make_player()
    p.update(1.0, Ctx(), Intent(left=1, right=0))
    assert p.vel_x == -200.0


def test_player_emits_jump_event_when_on_ground():
    from core.event_bus import GameEvents

    class FakeEventBus:
        def __init__(self):
            self.emitted = []

        def emit(self, event, *args):
            self.emitted.append(event)

    bus = FakeEventBus()
    p = make_player(event_bus=bus)
    p.on_ground = True
    p.update(1.0, Ctx(), Intent(jump_pressed=True))
    assert GameEvents.PLAYER_JUMP in bus.emitted


def test_player_does_not_jump_when_airborne():
    from core.event_bus import GameEvents

    class FakeEventBus:
        def __init__(self):
            self.emitted = []

        def emit(self, event, *args):
            self.emitted.append(event)

    bus = FakeEventBus()
    p = make_player(event_bus=bus)
    p.on_ground = False  # в воздухе
    p.update(1.0, Ctx(), Intent(jump_pressed=True))
    assert GameEvents.PLAYER_JUMP not in bus.emitted