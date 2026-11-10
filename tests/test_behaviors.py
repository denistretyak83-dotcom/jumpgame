"""Тесты поведений: FallDeathBehavior (смерть-падение) и CallableRespawnBehavior."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from models.behaviors import (  # noqa: E402
    DeathBehavior,
    RespawnBehavior,
    FallDeathBehavior,
    CallableRespawnBehavior,
)

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeOwner:
    """Минимальный владелец: rect и vel_x."""

    def __init__(self, y=100, vel_x=0.0):
        import pygame

        self.rect = pygame.Rect(0, y, 32, 48)
        self.vel_x = vel_x


class FakeDeathCfg:
    gravity = 1200
    margin = 60
    launch_vy = -400
    fall_vy = -100


# --------------------------------------------------------------------------
# FallDeathBehavior — конструктор и параметры
# --------------------------------------------------------------------------
def test_fall_death_defaults_without_cfg():
    b = FallDeathBehavior()
    assert b.death_gravity == 1200
    assert b.screen_height == 720
    assert b.margin == 60
    assert b.launch_vy == -400
    assert b.fall_vy == -100
    assert b.active is False
    assert b.death_vy == 0.0


def test_fall_death_reads_from_cfg():
    b = FallDeathBehavior(death_cfg=FakeDeathCfg(), screen_height=600)
    assert b.death_gravity == 1200
    assert b.margin == 60
    assert b.screen_height == 600


def test_fall_death_explicit_args_override_cfg():
    b = FallDeathBehavior(
        death_cfg=FakeDeathCfg(),
        death_gravity=999,
        margin=10,
        launch_vy=-50,
        fall_vy=-5,
        screen_height=500,
    )
    assert b.death_gravity == 999
    assert b.margin == 10
    assert b.launch_vy == -50
    assert b.fall_vy == -5
    assert b.screen_height == 500


# --------------------------------------------------------------------------
# FallDeathBehavior — die()
# --------------------------------------------------------------------------
def test_fall_death_initially_inactive():
    b = FallDeathBehavior()
    assert b.is_active is False


def test_die_without_owner_does_nothing():
    b = FallDeathBehavior()  # owner=None
    b.die()
    assert b.active is False
    assert b.is_active is False


def test_die_activates_and_sets_launch_up():
    owner = FakeOwner()
    b = FallDeathBehavior(owner=owner)
    b.die(launch_up=True)
    assert b.active is True
    assert b.death_vy == b.launch_vy  # вверх
    assert owner.vel_x == 0           # враг остановлен


def test_die_activates_and_sets_fall():
    owner = FakeOwner()
    b = FallDeathBehavior(owner=owner)
    b.die(launch_up=False)
    assert b.active is True
    assert b.death_vy == b.fall_vy    # вниз


# --------------------------------------------------------------------------
# FallDeathBehavior — update()
# --------------------------------------------------------------------------
def test_update_returns_false_when_inactive():
    owner = FakeOwner()
    b = FallDeathBehavior(owner=owner)
    # не вызывали die -> не активен
    assert b.update(0.016) is False


def test_update_moves_owner_down():
    owner = FakeOwner(y=0)
    b = FallDeathBehavior(owner=owner, screen_height=600, margin=60)
    b.die(launch_up=False)   # fall_vy=-100, но gravity добавит массу
    y0 = owner.rect.y
    for _ in range(10):
        finished = b.update(0.016)
        if finished:
            break
    # с нарастающей гравитацией персонаж должен продвинуться вниз за время
    assert owner.rect.y > y0


def test_update_finishes_when_below_screen():
    import pygame

    owner = FakeOwner(y=1000)  # уже ниже экрана 600+60
    b = FallDeathBehavior(owner=owner, screen_height=600, margin=60)
    owner.rect = pygame.Rect(0, 600, 32, 48)
    b.die(launch_up=False)
    # owner.rect.top = 600, screen+margin=660 -> ещё не завершено
    assert b.update(0.016) is False
    # сдвигаем далеко вниз — теперь завершено
    owner.rect.y = 700
    assert b.update(0.016) is True


def test_die_with_launch_up_then_update_can_rise_first():
    owner = FakeOwner(y=100)
    b = FallDeathBehavior(
        owner=owner, screen_height=600, margin=60,
        death_gravity=0, launch_vy=-100,  # без гравитации: чисто вверх/вниз
    )
    b.die(launch_up=True)
    b.update(1.0)
    # запуск вверх: смерть_vy=-100, dt=1 -> смещение вверх
    assert owner.rect.y < 100


# --------------------------------------------------------------------------
# CallableRespawnBehavior
# --------------------------------------------------------------------------
def test_callable_respawn_spawn_copy_calls_factory():
    result = "new_character"
    b = CallableRespawnBehavior(factory=lambda: result)
    assert b.spawn_copy() is result


def test_callable_respawn_uses_fresh_factory_each_time():
    counter = {"n": 0}

    def factory():
        counter["n"] += 1
        return f"copy-{counter['n']}"

    b = CallableRespawnBehavior(factory=factory)
    assert b.spawn_copy() == "copy-1"
    assert b.spawn_copy() == "copy-2"


# --------------------------------------------------------------------------
# Абстрактные базовые классы не инстанцируются
# --------------------------------------------------------------------------
def test_abstract_behaviors_cannot_be_instantiated():
    with pytest.raises(TypeError):
        DeathBehavior()
    with pytest.raises(TypeError):
        RespawnBehavior()