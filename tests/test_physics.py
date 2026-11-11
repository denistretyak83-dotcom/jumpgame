"""Тесты PhysicsComponent: гравитация, clamp max_fall, коллизии, grounded."""
import importlib.util

import pytest

# Всё содержимое наполняется через реальный pygame.Rect (headless-режим).
# Если pygame недоступен в окружении — тесты пропускаются.
pygame_available = importlib.util.find_spec("pygame") is not None

from models.physics import PhysicsComponent, PhysicsParams  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен для pygame.Rect)"
)


# --------------------------------------------------------------------------
# Фейковый «владелец» физики: имитирует BaseCharacter-интерфейс.
# --------------------------------------------------------------------------
class FakeOwner:
    def __init__(self, x=0, y=0, w=32, h=48, vel_x=0.0, vel_y=0.0):
        import pygame

        self.rect = pygame.Rect(x, y, w, h)
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.on_ground = False
        self.is_dead = False


# --------------------------------------------------------------------------
# PhysicsParams
# --------------------------------------------------------------------------
def test_params_defaults():
    p = PhysicsParams()
    assert p.gravity == 1500
    assert p.max_fall == 1400
    assert abs(p.ground_tolerance - 8.0) < 1e-9


def test_params_custom_values():
    p = PhysicsParams(gravity=100, max_fall=50, ground_tolerance=3.0)
    assert p.gravity == 100
    assert p.max_fall == 50
    assert p.ground_tolerance == 3.0


# --------------------------------------------------------------------------
# _resolve_* — берут значение из PhysicsParams или cfg.physics
# --------------------------------------------------------------------------
def test_resolve_from_params():
    pc = PhysicsComponent(config=PhysicsParams(gravity=900, max_fall=600))
    assert pc._gravity == 900
    assert pc._max_fall == 600
    # ground_tolerance в PhysicsParams есть — берём его
    assert pc._ground_tolerance == 8.0


class FakePhysicsCfg:
    gravity = 111
    max_fall = 222


class FakeSettings:
    physics = FakePhysicsCfg


def test_resolve_from_external_config():
    # cfg.physics есть -> берём оттуда gravity/max_fall, а tolerance уходит в дефолт
    pc = PhysicsComponent(config=FakeSettings())
    assert pc._gravity == 111
    assert pc._max_fall == 222
    assert pc._ground_tolerance == PhysicsParams.ground_tolerance


def test_resolve_fallback_when_config_empty():
    # config без атрибута physics -> все из дефолтов PhysicsParams
    pc = PhysicsComponent(config=object())
    assert pc._gravity == PhysicsParams.gravity
    assert pc._max_fall == PhysicsParams.max_fall
    assert pc._ground_tolerance == PhysicsParams.ground_tolerance


# --------------------------------------------------------------------------
# apply — гравитация и clamp по max_fall
# --------------------------------------------------------------------------
def test_apply_adds_gravity_when_airborne():
    pc = PhysicsComponent()  # gravity=1500
    owner = FakeOwner(vel_y=0.0)
    pc.apply(owner, dt=0.1, platforms=[])
    # vel_y растёт вниз: 0 + 1500*0.1 = 150
    assert owner.vel_y == pytest.approx(150.0, abs=1e-6)
    assert not owner.on_ground


def test_apply_clamps_velocity_to_max_fall():
    # маленький dt, но много шагов -> vel_y не превысит max_fall
    pc = PhysicsComponent()  # max_fall=1400
    owner = FakeOwner(vel_y=1390.0)
    for _ in range(10):
        pc.apply(owner, dt=0.5, platforms=[])
    assert owner.vel_y <= 1400.0 + 1e-9


def test_apply_does_nothing_when_dead():
    pc = PhysicsComponent()
    owner = FakeOwner(vel_y=0.0)
    owner.is_dead = True
    result = pc.apply(owner, dt=0.1, platforms=[])
    assert result is False
    assert owner.vel_y == 0.0


# --------------------------------------------------------------------------
# apply — приземление на платформу (стоп падение, on_ground=True)
# --------------------------------------------------------------------------
def test_apply_lands_on_platform_top():
    import pygame

    pc = PhysicsComponent()
    dt = 1 / 60
    owner = FakeOwner(x=0, y=100, w=32, h=48, vel_y=0.0)
    platform = pygame.Rect(0, 200, 200, 20)
    for _ in range(120):
        pc.apply(owner, dt, [platform])
        if owner.on_ground:
            break
    # Игрок встал на платформу: основание равно её верхушке, скорость обнулена
    assert owner.rect.bottom == 200
    assert owner.vel_y == 0
    assert owner.on_ground is True


def test_apply_reports_head_bump():
    import pygame

    pc = PhysicsComponent()
    dt = 1 / 60
    # Игрок прыгает вверх, над ним платформа-потолок
    owner = FakeOwner(x=0, y=300, w=32, h=48, vel_x=0.0, vel_y=-1500.0)
    platform = pygame.Rect(0, 220, 200, 20)  # потолок
    bumped = False
    for _ in range(60):
        result = pc.apply(owner, dt, [platform])
        if result:
            bumped = True
            break
    assert bumped is True
    assert owner.vel_y == 0


# --------------------------------------------------------------------------
# apply — горизонтальное смещение
# --------------------------------------------------------------------------
def test_apply_moves_horizontally():
    pc = PhysicsComponent()
    owner = FakeOwner(x=0, y=0, vel_x=100.0)
    pc.apply(owner, dt=1.0, platforms=[])
    # vel_x=100, dt=1 -> смещение на 100
    assert owner.rect.x == 100


def test_apply_stops_at_wall_from_left():
    import pygame

    pc = PhysicsComponent()
    dt = 1 / 60
    # Игрок стоит на "полу" (чтобы не упасть) и идёт вправо в стену
    owner = FakeOwner(x=0, y=200, w=32, h=48, vel_x=200.0, vel_y=0.0)
    floor = pygame.Rect(0, 300, 500, 20)
    wall = pygame.Rect(250, 0, 20, 300)  # стена справа перед игроком
    for _ in range(120):
        pc.apply(owner, dt, [floor, wall])
    # правый край игрока упёрся в левый край стены
    assert owner.rect.right == wall.left


def test_apply_stops_at_wall_from_right():
    import pygame

    pc = PhysicsComponent()
    dt = 1 / 60
    # Игрок на полу идёт влево в стену
    owner = FakeOwner(x=500, y=200, w=32, h=48, vel_x=-200.0, vel_y=0.0)
    floor = pygame.Rect(0, 300, 700, 20)
    wall = pygame.Rect(250, 0, 20, 300)  # стена слева
    for _ in range(120):
        pc.apply(owner, dt, [floor, wall])
    assert owner.rect.left == wall.right


# --------------------------------------------------------------------------
# update_grounded — расчёт on_ground по допуску
# --------------------------------------------------------------------------
def test_update_grounded_true_when_on_platform():
    import pygame

    pc = PhysicsComponent()
    owner = FakeOwner(x=0, y=52, w=32, h=48, vel_y=0.0)  # bottom=100
    platform = pygame.Rect(0, 100, 200, 20)
    pc.update_grounded(owner, platforms=[platform])
    assert owner.on_ground is True


def test_update_grounded_false_when_above():
    import pygame

    pc = PhysicsComponent()
    owner = FakeOwner(x=0, y=40, w=32, h=48, vel_y=0.0)  # bottom=88
    platform = pygame.Rect(0, 100, 200, 20)
    pc.update_grounded(owner, platforms=[platform])
    assert owner.on_ground is False


def test_update_grounded_false_when_below_tolerance():
    import pygame

    pc = PhysicsComponent(PhysicsParams(ground_tolerance=8.0))
    # bottom=150 — далеко под верхушкой платформы (100) — не grounded
    owner = FakeOwner(x=0, y=102, w=32, h=48, vel_y=0.0)
    platform = pygame.Rect(0, 100, 200, 20)
    pc.update_grounded(owner, platforms=[platform])
    assert owner.on_ground is False

# --------------------------------------------------------------------------
# Контракты-протоколы физики (Фаза 3, 4.3)
# --------------------------------------------------------------------------
from models.physics import PhysicsBody, PhysicsEngine


class FakeBody:
    def __init__(self):
        self.rect = None
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.is_dead = False


def test_physics_component_satisfies_engine_protocol():
    assert isinstance(PhysicsComponent(), PhysicsEngine)


def test_physics_engine_protocol_detects_missing_method():
    class NoImpl:
        pass

    assert not isinstance(NoImpl(), PhysicsEngine)


def test_physics_body_protocol_atttributes_present():
    b = FakeBody()
    for attr in ("rect", "vel_x", "vel_y", "on_ground", "is_dead"):
        assert hasattr(b, attr)