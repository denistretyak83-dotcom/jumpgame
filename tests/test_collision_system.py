"""Тесты CollisionSystem: монеты, враги, флаг, падение за экран.

Фаза 4: коллизии работают на core.geometry.RectPosition (без pygame).
"""
import pytest

from core.geometry import RectPosition
from models.collision_system import CollisionSystem, CollisionResult  # noqa: E402


class FakeCollidable:
    """Объект с .rect, удовлетворяющий Collidable (Protocol)."""

    def __init__(self, rect):
        self.rect = rect


def make_system(screen_height=600, fall_buffer=50):
    return CollisionSystem(screen_height=screen_height, fall_buffer=fall_buffer)


def test_no_collisions_returns_empty_result():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    result = sys.check(
        player_rect=player,
        coins=[RectPosition(500, 500, 16, 16)],
        coin_collected=[False],
        enemies=[FakeCollidable(RectPosition(700, 10, 20, 20))],
        flag_rect=RectPosition(900, 900, 40, 60),
    )
    assert result.coin_index is None
    assert result.hit_enemy is None
    assert result.hit_flag is False
    assert result.fell_out is False


def test_coin_collision_detects_index():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    coins = [
        RectPosition(500, 500, 16, 16),
        RectPosition(10, 10, 16, 16),   # пересекается с игроком
    ]
    result = sys.check(player, coins, [False, False], [], None)
    assert result.coin_index == 1


def test_coin_collision_skips_collected():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    coins = [RectPosition(10, 10, 16, 16),
             RectPosition(5, 5, 16, 16)]
    # первая монета уже собрана (coin_collected[0]=True), вторая нет
    result = sys.check(player, coins, [True, False], [], None)
    assert result.coin_index == 1


def test_enemy_collision_detected():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    enemy_rect = RectPosition(5, 5, 32, 48)
    enemy = FakeCollidable(enemy_rect)
    result = sys.check(player, [], [], [enemy], None)
    assert result.hit_enemy is enemy


def test_enemy_collision_first_one_wins():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    e1 = FakeCollidable(RectPosition(5, 5, 32, 48))      # пересекается
    e2 = FakeCollidable(RectPosition(900, 900, 32, 48))  # нет
    result = sys.check(player, [], [], [e1, e2], None)
    assert result.hit_enemy is e1


def test_flag_collision_detected():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    flag = RectPosition(2, 2, 40, 60)
    result = sys.check(player, [], [], [], flag)
    assert result.hit_flag is True


def test_does_not_hit_flag_when_no_intersection():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    flag = RectPosition(900, 900, 40, 60)
    result = sys.check(player, [], [], [], flag)
    assert result.hit_flag is False


def test_flag_none_is_safe():
    import pygame

    sys = make_system()
    player = RectPosition(0, 0, 32, 48)
    result = sys.check(player, [], [], [], None)
    assert result.hit_flag is False


def test_fell_out_when_below_screen_plus_buffer():
    import pygame

    sys = make_system(screen_height=600, fall_buffer=50)
    player = RectPosition(0, 700, 32, 48)   # bottom=748 > 650
    result = sys.check(player, [], [], [], None)
    assert result.fell_out is True


def test_not_fell_out_within_buffer():
    import pygame

    sys = make_system(screen_height=600, fall_buffer=50)
    player = RectPosition(0, 600, 32, 40)   # bottom=640 <= 650
    result = sys.check(player, [], [], [], None)
    assert result.fell_out is False


def test_multi_collision_all_results_together():
    import pygame

    sys = make_system(screen_height=600, fall_buffer=50)
    player = RectPosition(0, 700, 32, 48)  # упал (bottom=748)
    coin = RectPosition(2, 700, 16, 16)     # пересекается
    flag = RectPosition(1, 700, 40, 60)     # пересекается
    enemy = FakeCollidable(RectPosition(0, 700, 32, 48))
    result = sys.check(player, [coin], [False], [enemy], flag)
    assert result.coin_index == 0
    assert result.hit_enemy is enemy
    assert result.hit_flag is True
    assert result.fell_out is True