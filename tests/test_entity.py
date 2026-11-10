"""Тесты геометрии Entity (models/entity.py). Требуют pygame (headless по conftest)."""
import pygame

from models.entity import Entity


def test_entity_initializes_rect():
    e = Entity(10, 20, 40, 50)
    assert isinstance(e.rect, pygame.Rect)
    assert (e.x, e.y) == (10, 20)
    assert (e.width, e.height) == (40, 50)


def test_properties_sync_with_rect():
    e = Entity(0, 0, 100, 60)
    assert (e.left, e.top) == (0, 0)
    assert (e.right, e.bottom) == (100, 60)
    assert (e.centerx, e.centery) == (50, 30)


def test_setters_touch_internal_rect():
    e = Entity(0, 0, 10, 10)
    e.x = 5
    e.y = 7
    e.width = 20
    e.height = 30
    assert e.rect.x == 5
    assert e.rect.y == 7
    assert e.rect.width == 20
    assert e.rect.height == 30


def test_edge_properties_write_back():
    e = Entity(0, 0, 100, 60)
    e.right = 200      # width становится 200 (left=0)
    assert e.width == 200
    e.top = 10
    assert e.y == 10
