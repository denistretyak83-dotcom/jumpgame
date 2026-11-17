"""Фаза 9: ViewFactory изолирует OCP-регистрацию вью от Game.

Проверяем:
  - Player сопоставляется с player_view() (через реестр);
  - Enemy сопоставляется с enemy_view() (резерв по OCP);
  - register() добавляет новый тип без правки Renderer/Game;
  - реестр отдаёт кэшированный вью (та же ссылка для Player).
"""

import pytest

from models.enemy import Enemy
from models.player import Player
from views.sprite_cache import SpriteCache
from views.view_factory import ViewFactory


class _FakeAssets:
    """Подмена AssetLoader: пустые кадры (Animation терпит len==0)."""
    def load_animation_frames(self, key, count, size):
        return []


class _FakeConfig:
    class _anim:
        idle_delay = 0.1
        run_delay = 0.1
        walk_delay = 0.15
        jump_delay = 0.1
    animation = _anim()

    class _player:
        width = 16
        height = 24
    player = _player()

    class _enemy:
        width = 16
        height = 16
    enemy = _enemy()


@pytest.fixture
def view_factory():
    sprite_cache = SpriteCache(_FakeAssets(), _FakeConfig())
    return ViewFactory(sprite_cache)


def test_factory_maps_player_to_player_view(view_factory):
    reg = view_factory.build_default_registry()
    assert Player in reg
    view = reg[Player]()
    assert view is not None
    assert view.__class__.__name__ == "CharacterView"


def test_factory_maps_enemy_to_enemy_view(view_factory):
    reg = view_factory.build_default_registry()
    assert Enemy in reg
    view = reg[Enemy]()
    assert view is not None
    assert view.__class__.__name__ == "CharacterView"


def test_factory_player_view_is_cached(view_factory):
    reg = view_factory.build_default_registry()
    a = reg[Player]()
    b = reg[Player]()
    assert a is b  # SpriteCache кэширует одиночный вью игрока


def test_factory_register_new_type_ocp(view_factory):
    class MyCreature:  # новый тип сущности -- не Player/Enemy
        pass

    calls = []

    def make_view():
        calls.append(1)
        return "view_obj"

    view_factory.register(MyCreature, make_view)
    assert view_factory.registry[MyCreature]() == "view_obj"
    assert calls == [1]


def test_factory_registry_is_copy(view_factory):
    reg = view_factory.build_default_registry()
    reg["external_key"] = object()  # внешние мутации не портят внутренний реестр
    assert "external_key" not in view_factory.registry