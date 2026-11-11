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

# ---------------------------------------------------------------------------
# Фаза 4 добавки: bounds-сеттеры, пересечения по краям/оси, negative coords,
# float-точность, алиасы colliderect/move, contains_point границы.
# ---------------------------------------------------------------------------

def test_edge_setters_right_bottom() -> None:
    r = RectPosition(0, 0, 100, 60)
    r.right = 200
    assert r.x == 100
    assert r.width == 100      # размер не меняется
    r.bottom = 400
    assert r.y == 340
    assert r.height == 60


def test_edge_setters_top_left() -> None:
    r = RectPosition(10, 20, 30, 40)
    r.left = 5
    assert r.x == 5
    assert r.width == 30
    r.top = 7
    assert r.y == 7
    assert r.height == 40


def test_center_setters_keep_size() -> None:
    r = RectPosition(0, 0, 100, 200)
    r.centerx = 500
    r.centery = 700
    assert r.centerx == 500
    assert r.centery == 700
    assert r.x == 450          # 500 - 50
    assert r.y == 600          # 700 - 100
    assert r.width == 100
    assert r.height == 200


def test_intersects_vertical_overlap_only() -> None:
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(20, 5, 10, 10)
    assert a.intersects(b) is False


def test_intersects_horizontal_overlap_only() -> None:
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(5, 20, 10, 10)
    assert a.intersects(b) is False


def test_intersects_contained_is_true() -> None:
    a = RectPosition(0, 0, 100, 100)
    b = RectPosition(20, 20, 10, 10)
    assert a.intersects(b) is True
    assert b.intersects(a) is True


def test_intersects_touching_corner_is_false() -> None:
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(10, 10, 10, 10)
    assert a.intersects(b) is False


def test_intersects_floats() -> None:
    a = RectPosition(0.0, 0.0, 10.5, 10.5)
    b = RectPosition(10.0, 5.0, 5.0, 5.0)
    assert a.intersects(b) is True


def test_contains_point_inclusive_edges() -> None:
    r = RectPosition(0, 0, 100, 60)
    assert r.contains_point(0, 0) is True
    assert r.contains_point(100, 60) is True
    assert r.contains_point(-0.1, 30) is False
    assert r.contains_point(50, 30) is True


def test_negative_coordinates() -> None:
    r = RectPosition(-50, -20, 100, 60)
    assert r.right == 50
    assert r.bottom == 40
    assert r.centerx == 0
    assert r.centery == 10
    assert r.intersects(RectPosition(-10, -5, 10, 10)) is True
    assert r.contains_point(0, 10) is True


def test_colliderect_alias_matches_intersects() -> None:
    a = RectPosition(0, 0, 10, 10)
    b = RectPosition(5, 5, 10, 10)
    c = RectPosition(50, 50, 10, 10)
    assert a.colliderect(b) is a.intersects(b) is True
    assert a.colliderect(c) is a.intersects(c) is False


def test_move_returns_new_rect_not_mutating() -> None:
    a = RectPosition(10, 10, 20, 20)
    b = a.move(5, -5)
    assert (b.x, b.y) == (15, 5)
    assert (a.x, a.y) == (10, 10)


def test_move_ip_mutates_in_place() -> None:
    a = RectPosition(10, 10, 20, 20)
    a.move_ip(3, 4)
    assert (a.x, a.y) == (13, 14)


def test_float_precision_computed_edges() -> None:
    r = RectPosition(1.5, 2.5, 3.5, 4.5)
    assert abs(r.right - 5.0) < 1e-9
    assert abs(r.bottom - 7.0) < 1e-9
    assert abs(r.centerx - 3.25) < 1e-9
    assert abs(r.centery - 4.75) < 1e-9
