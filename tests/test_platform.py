"""Тесты Platform (Фаза 5, задача C): типизированные платформы.

Проверяют модель Platform (rect + tile_style), чтение стиля из данных,
default-стиль, rect4-совместимость и OCP-регистрацию подтипов в WorldFactory.
"""
import pytest

from core.geometry import RectPosition
from models.platform import Platform


def test_platform_holds_rect_and_style():
    p = Platform(rect=RectPosition(10, 20, 100, 30), tile_style="brick")
    assert isinstance(p.rect, RectPosition)
    assert p.rect.x == 10 and p.rect.y == 20
    assert p.rect.width == 100 and p.rect.height == 30
    assert p.tile_style == "brick"


def test_platform_default_style_is_grass_top():
    p = Platform(rect=RectPosition(0, 0, 40, 30))
    assert p.tile_style == "grass_top"


def test_platform_delegates_geometry_to_rect():
    p = Platform(rect=RectPosition(0, 540, 200, 30))
    assert p.x == 0 and p.y == 540
    assert p.width == 200 and p.height == 30
    assert p.left == 0 and p.top == 540
    assert p.right == 200 and p.bottom == 570
    assert p.centerx == 100 and p.centery == 555


def test_platform_rect4_protocol():
    p = Platform(rect=RectPosition(0, 540, 200, 30))
    assert tuple(p)[:4] == (0, 540, 200, 30)
    assert list(p) == [0, 540, 200, 30]
    assert len(p) == 4
    assert p[0] == 0 and p[1] == 540 and p[2] == 200 and p[3] == 30


def test_platform_is_pygame_rect_compatible():
    import importlib.util
    if importlib.util.find_spec("pygame") is None:
        pytest.skip("pygame недоступен")
    import pygame
    p = Platform(rect=RectPosition(0, 540, 200, 30))
    pr = pygame.Rect(p)
    assert (pr.x, pr.y, pr.width, pr.height) == (0, 540, 200, 30)
    player = pygame.Rect(50, 510, 35, 35)
    assert player.colliderect(p) is True


def _make_factory():
    from models.factory import WorldFactory
    return WorldFactory(object())


def test_factory_builds_platform_with_style():
    factory = _make_factory()
    p = factory.create("platform", {"x": 0, "y": 540, "w": 200, "h": 30, "style": "brick"})
    assert isinstance(p, Platform)
    assert p.tile_style == "brick"
    assert p.rect.x == 0 and p.rect.width == 200


def test_factory_platform_default_style():
    factory = _make_factory()
    p = factory.create("platform", {"x": 0, "y": 540, "w": 200, "h": 30})
    assert p.tile_style == "grass_top"
    assert p.rect.height == 30


def test_factory_platform_missing_rect_keys_raises():
    factory = _make_factory()
    with pytest.raises(ValueError):
        factory.create("platform", {"x": 0, "y": 540})


def test_ocp_register_platform_subtype():
    factory = _make_factory()

    def ice_platform(data):
        rect = RectPosition(int(data["x"]), int(data["y"]), int(data["w"]), int(data["h"]))
        return Platform(rect=rect, tile_style="ice")

    factory.register("platform/ice", ice_platform)
    p = factory.create("platform/ice", {"x": 5, "y": 5, "w": 100, "h": 20})
    assert isinstance(p, Platform)
    assert p.tile_style == "ice"
    assert p.rect.x == 5


def test_entity_factories_expose_platform():
    factory = _make_factory()
    assert "platform" in factory.entity_factories()