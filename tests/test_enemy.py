"""Тесты Enemy: конструктор, выбор поведения, движение через update."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from models.enemy import Enemy  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeEnemyCfg:
    class EnemyParams:
        width = 32
        height = 48
        speed = 10.0

    enemy = EnemyParams()


def make_enemy(behavior="walker", x=0, y=0, left=0, right=300, **data):
    d = {"behavior": behavior}
    d.update(data)
    return Enemy(x, y, left, right, FakeEnemyCfg(), enemy_data=d)


def test_enemy_default_behavior_is_walker():
    e = make_enemy(x=0)
    assert e.behavior_type == "walker"
    # поведение привязано, враг имеет границы
    assert e.bound_left == 0
    assert e.bound_right == 300


def test_enemy_takes_behavior_from_data():
    e = make_enemy(behavior="chaser", x=0)
    assert e.behavior_type == "chaser"


def test_enemy_unknown_behavior_falls_back_to_walker():
    # реестр DEFAULT имеет fallback на walker
    e = make_enemy(behavior="no_such_behavior", x=0)
    assert e.behavior_type == "no_such_behavior"  # тип сохраняется как есть
    # но поведение — walker (т.к. регистрация неизвестного -> fallback)
    # проверим, что враг движется как патруль
    e.update(1.0)
    assert e.pos_x == pytest.approx(10.0)


def test_enemy_update_moves_via_behavior():
    e = make_enemy(behavior="walker", x=0, speed=10.0)
    e.update(dt=1.0)
    assert e.pos_x == pytest.approx(10.0)
    assert e.rect.x == int(round(e.pos_x))


def test_enemy_get_visual_data():
    e = make_enemy(behavior="walker", x=5, sprite="flyer")
    vd = e.get_visual_data()
    assert vd.x == 5
    assert vd.width == 32
    assert vd.height == 48
    assert vd.anim_group == "flyer"   # из sprite -> anim_group
    assert vd.facing_left is False    # vel_x > 0


def test_enemy_honors_type_and_size_override():
    # Поведение flyer из-за "type" НЕ должен мешать; размер переопределяется w/h.
    e = make_enemy(behavior="walker", x=0, y=0, left=0, right=300, type="elite", w=50, h=70)
    assert e.entity_type == "elite"
    assert e.rect.width == 50
    assert e.rect.height == 70


def test_enemy_default_type_and_size():
    e = make_enemy(behavior="walker", x=0)
    assert e.entity_type == "enemy"
    assert e.rect.width == FakeEnemyCfg.enemy.width == 32
    assert e.rect.height == FakeEnemyCfg.enemy.height == 48