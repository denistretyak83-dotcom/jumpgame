"""Тесты RectPosition: геометрия без pygame (Фаза 4)."""
import importlib.util

import pytest

from core.geometry import RectPosition


def test_rect_position_defaults():
    r = RectPosition(10, 20, 100, 50)
    assert r.x == 10
    assert r.y == 20
    assert r.width == 100
    assert r.height == 50


def test_computed_properties():
    r = RectPosition(0, 0, 100, 60)
    assert r.right == 100
    assert r.bottom == 60
    assert r.centerx == 50
    assert r.centery == 30
    assert r.left == 0
    assert r.top == 0


def test_intersects_overlapping():
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(5, 5, 10, 10)
    assert a.intersects(b) is True


def test_intersects_no_overlap():
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(20, 20, 10, 10)
    assert a.intersects(b) is False


def test_intersects_touching_edge_is_false():
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(10, 0, 10, 10)   # касание по правому краю
    assert a.intersects(b) is False


def test_contains_point():
    r = RectPosition(0, 0, 100, 60)
    assert r.contains_point(50, 30) is True
    assert r.contains_point(150, 30) is False


def test_to_pygame_rect_when_pygame_available():
    pygame_available = importlib.util.find_spec("pygame") is not None
    if not pygame_available:
        pytest.skip("pygame недоступен")
    r = RectPosition(1.9, 2.9, 10.4, 5.6)
    pr = r.to_pygame_rect()
    assert pr.x == 1
    assert pr.y == 2
    assert pr.width == 10
    assert pr.height == 5