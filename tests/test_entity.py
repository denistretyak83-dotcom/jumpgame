"""Тесты Entity: инкапсуляция 9-ти properties и синхронизация с внутренним rect.

Свойства делегируют в pygame.Rect (см. models.entity). Семантика сеттеров —
стандартная pygame: right/bottom/center двигают позицию, сохраняя размер.
"""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from models.entity import Entity  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


def test_entity_initializes_rect():
    e = Entity(10, 20, 100, 60)
    assert e.rect.x == 10
    assert e.rect.y == 20
    assert e.rect.width == 100
    assert e.rect.height == 60


def test_properties_sync_with_rect():
    e = Entity(10, 20, 100, 60)
    # позиция
    assert e.x == 10 and e.y == 20
    # размер
    assert e.width == 100 and e.height == 60
    # левая/верхняя
    assert e.left == 10 and e.top == 20
    # правая/нижняя
    assert e.right == 110 and e.bottom == 80
    # центр
    assert e.centerx == 60 and e.centery == 50


def test_position_setters_update_rect():
    e = Entity(10, 20, 100, 60)
    e.x = 5
    e.y = 7
    e.width = 200
    e.height = 90
    assert e.rect.x == 5
    assert e.rect.y == 7
    assert e.rect.width == 200
    assert e.rect.height == 90


def test_edge_setters_move_position_keep_size():
    e = Entity(0, 0, 100, 60)
    # right двигает позицию
    e.right = 200
    assert e.right == 200
    assert e.width == 100
    assert e.left == 100
    # bottom двигает позицию
    e.bottom = 400
    assert e.bottom == 400
    assert e.height == 60
    assert e.top == 340


def test_center_setters():
    e = Entity(0, 0, 100, 200)
    e.centerx = 500
    e.centery = 700
    assert e.centerx == 500
    assert e.centery == 700
    assert e.left == 450      # 500 - 50
    assert e.top == 600       # 700 - 100
    assert e.width == 100     # размеры не меняются
    assert e.height == 200


def test_left_top_setters():
    e = Entity(10, 20, 100, 60)
    e.left = 30
    e.top = 40
    assert e.left == 30
    assert e.top == 40
    assert e.x == 30 and e.y == 40
    assert e.width == 100 and e.height == 60


def test_width_height_setters_keep_origin():
    e = Entity(10, 20, 100, 60)
    e.width = 250
    e.height = 90
    assert e.left == 10       # левый край не двигался
    assert e.top == 20
    assert e.right == 260
    assert e.bottom == 110