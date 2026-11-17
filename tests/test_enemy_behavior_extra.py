"""Фаза 12: расширяемость реестра поведений — ZigzagBehavior (OCP)."""

import pytest

from core.geometry import RectPosition
from models.enemy_behavior import EnemyBehaviorRegistry
from models.enemy_behaviors_extra import ZigzagBehavior


class _Ctx:
    def __init__(self, player_x):
        self.player_x = player_x


class FakeEnemy:
    """Объект-враг, удовлетворяющий тому минимуму, что нужно ZigzagBehavior."""

    def __init__(self, x=0, y=100, w=32, h=32, bound_left=0, bound_right=500, vel_x=30):
        self.rect = RectPosition(x, y, w, h)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.bound_left = bound_left
        self.bound_right = bound_right
        self.vel_x = float(vel_x)


def test_zigzag_registered_in_new_registry():
    reg = EnemyBehaviorRegistry()
    reg.register("zigzag", ZigzagBehavior)
    # реестр с одним fallback "walker"? По умолчанию fallback "walker".
    # Нужен walker, чтобы create не падал при отсутствии. Проверим напрямую:
    reg.register("walker", ZigzagBehavior)  # fallback тоже укажем на Zigzag для простоты
    behavior = reg.create("zigzag")
    assert isinstance(behavior, ZigzagBehavior)


def test_zigzag_moves_along_x_axis():
    behavior = ZigzagBehavior()
    enemy = FakeEnemy(x=50, y=100, vel_x=20, bound_right=500)
    behavior.attach(enemy)
    behavior.update(enemy, dt=1.0)
    # движение вправо должно увеличить x
    assert enemy.rect.x > 50


def test_zigzag_bounces_off_right_bound():
    behavior = ZigzagBehavior()
    enemy = FakeEnemy(x=490, y=100, vel_x=20, bound_right=500)
    behavior.attach(enemy)
    behavior.update(enemy, dt=1.0)
    # правый край не выходит за bound_right
    assert enemy.rect.x + enemy.rect.width <= enemy.bound_right


def test_zigzag_moves_along_y_axis():
    behavior = ZigzagBehavior()
    enemy = FakeEnemy(x=50, y=100, vel_x=0)
    behavior.attach(enemy)
    behavior.update(enemy, dt=0.5)
    # Y-рывок вниз (y_dir=1) -> rect.y растёт
    assert enemy.rect.y > 100


def test_zigzag_bounces_within_y_range():
    behavior = ZigzagBehavior(zig_range=40)
    enemy = FakeEnemy(x=50, y=100, vel_x=0)
    behavior.attach(enemy)
    for _ in range(100):
        behavior.update(enemy, dt=1.0)
    # Y остаётся в пределах base_y ± range
    assert abs(enemy.rect.y) <= 100 + 40 + 1e-6