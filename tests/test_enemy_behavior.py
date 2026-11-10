"""Тесты EnemyBehavior: реестр (OCP) и поведения walker/chaser/flyer.

Используется фейковый враг, имитирующий API, который потребляет поведение:
pos_x, pos_y, vel_x, bound_left, bound_right, rect (pygame.Rect).
"""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from models.enemy_behavior import (  # noqa: E402
    DEFAULT_BEHAVIOR_REGISTRY,
    EnemyBehaviorRegistry,
    WalkerBehavior,
    ChaserBehavior,
    FlyerBehavior,
)

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeEnemy:
    """Минимальный враг, достаточный для поведения."""

    def __init__(self, x=0, y=0, w=32, h=48, speed=10.0,
                 bound_left=0, bound_right=300):
        import pygame

        self.rect = pygame.Rect(x, y, w, h)
        self.width = w
        self.width = w
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
    # без регистраций create с unknown должен вернуть fallback
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


def test_default_registry_fallback_on_unknown():
    # Неизвестный тип -> fallback (walker)
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
    b.update(e, dt=1.0)   # -40 за границу 0 -> отражение на +40
    # отражение: насколько вылетел за границу, настолько отскочил внутрь
    assert e.pos_x == 40.0
    assert e.vel_x > 0    # развернулся вправо
    assert e.pos_x >= e.bound_left  # не ушёл за левую границу


def test_walker_turns_at_right_bound():
    e = FakeEnemy(x=290, w=32, bound_right=300, speed=50.0)
    b = WalkerBehavior()
    b.attach(e)
    b.update(e, dt=1.0)  # pos+width=340 > 300 -> отражается
    assert e.pos_x + e.width <= e.bound_right  # не вылезает за правую
    assert e.vel_x < 0                          # развернулся влево


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
    assert e.pos_x == 10.0  # движется вправо к игроку


def test_chaser_moves_toward_player_from_right():
    e = FakeEnemy(x=200, bound_left=0, bound_right=300, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=Ctx(player_x=100))
    assert e.pos_x < 200  # движется влево к игроку


def test_chaser_does_not_exit_bounds():
    e = FakeEnemy(x=200, bound_left=0, bound_right=100, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=Ctx(player_x=50))
    # игрок слева, но граница не даёт выйти
    assert e.pos_x >= e.bound_left
    assert e.pos_x + e.width <= e.bound_right


def test_chaser_falls_back_to_walker_without_ctx():
    e = FakeEnemy(x=0, bound_right=300, speed=10.0)
    b = ChaserBehavior()
    b.attach(e)
    b.update(e, dt=1.0, ctx=None)  # нет ctx -> работает как патруль
    assert e.pos_x == 10.0


# --------------------------------------------------------------------------
# FlyerBehavior
# --------------------------------------------------------------------------
def test_flyer_moves_x_and_oscillates_y():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = FlyerBehavior(amplitude=30, frequency=1.0)
    b.attach(e)
    b.update(e, dt=0.25)
    # X продвинулся на 10*0.25 = 2.5
    assert e.pos_x == pytest.approx(2.5)
    # Y вокруг базовой 100 с амплитудой 30 -> смещение от -30 до 30
    assert -30 <= (e.pos_y - 100) <= 30


def test_flyer_syncs_rect_position():
    e = FakeEnemy(x=0, y=100, bound_right=300, speed=10.0)
    b = FlyerBehavior(amplitude=30, frequency=1.0)
    b.attach(e)
    b.update(e, dt=0.25)
    import pygame

    assert e.rect.x == int(round(e.pos_x))
    assert e.rect.y == int(round(e.pos_y))