"""Тесты WorldFactory registry (models/factory.py). Требуют pygame (headless по conftest)."""
import pytest

from models.factory import WorldFactory


class _StubAssets:
    """Заглушка asset_loader — WorldFactory не использует его для register/create."""

    pass


@pytest.fixture
def factory():
    # config=None -> Settings() по умолчанию; запуск из корня проекта,
    # чтобы нашёлся config/settings.json.
    import os
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    return WorldFactory(_StubAssets())


def test_register_and_create_custom_type(factory):
    factory.register("gizmo", lambda data: ("gizmo", data["n"]))
    result = factory.create("gizmo", {"n": 42})
    assert result == ("gizmo", 42)


def test_create_platform_returns_rect(factory):
    rect = factory.create("platform", {"x": 0, "y": 540, "w": 200, "h": 30})
    assert rect.x == 0 and rect.y == 540
    assert rect.width == 200 and rect.height == 30


def test_create_unknown_type_raises(factory):
    with pytest.raises(KeyError):
        factory.create("nonexistent", {})


def test_entity_factories_expose_registered_types(factory):
    ef = factory.entity_factories()
    assert "platform" in ef
    assert "coin" in ef
    assert "enemy" in ef
