"""ФР-1: SpriteSource контракт + интеграция в SpriteCache (OCP)."""

import importlib.util

import pytest

from views.sprites.sprite_source import PngSpriteSource, SpriteSource


class _FakeAssets:
    def __init__(self):
        self.calls = []

    def load_animation_frames(self, folder, frame_count, scale):
        self.calls.append((folder, frame_count, scale))
        # фейковые кадры-поверхности заменить: вернём список фикционных объектов
        return ["frame"] * frame_count


class _FakeAnim:
    idle_delay = 0.1
    run_delay = 0.1
    walk_delay = 0.15
    jump_delay = 0.1


class _FakeCfg:
    animation = _FakeAnim()

    class _player:
        width = 40
        height = 50
    player = _player()

    class _enemy:
        width = 35
        height = 35
    enemy = _enemy()


def test_png_source_is_sprite_source_protocol():
    src = PngSpriteSource(_FakeAssets(), _FakeCfg())
    # isinstance по runtime_checkable Protocol
    assert isinstance(src, SpriteSource) is True


def test_png_source_size_returns_player_size():
    cfg = _FakeCfg()
    src = PngSpriteSource(_FakeAssets(), cfg)
    assert src.size() == (40, 50)


def test_png_source_supports_known_keys():
    src = PngSpriteSource(_FakeAssets(), _FakeCfg())
    assert src.supports("player_idle") is True
    assert src.supports("player_run/left") is True
    assert src.supports("enemy_walk") is True
    assert src.supports("nonexistent") is False


def test_png_source_frames_player_uses_player_size():
    assets = _FakeAssets()
    src = PngSpriteSource(assets, _FakeCfg())
    frames = src.frames("player_idle", 3)
    assert len(frames) == 3
    # размер из config.player
    assert assets.calls[-1][2] == (40, 50)


def test_png_source_frames_enemy_uses_enemy_size():
    assets = _FakeAssets()
    src = PngSpriteSource(assets, _FakeCfg())
    frames = src.frames("enemy_walk", 4)
    assert len(frames) == 4
    # размер из config.enemy
    assert assets.calls[-1][2] == (35, 35)


def test_sprite_cache_integrates_default_png_source():
    from views.sprite_cache import SpriteCache

    cache = SpriteCache(_FakeAssets(), _FakeCfg())
    # источник по умолчанию — PngSpriteSource (over) может быть свёрнуто
    assert isinstance(cache.default_source, PngSpriteSource)


def test_sprite_cache_register_and_switch_source():
    from views.sprites.sprite_source import PngSpriteSource
    from views.sprite_cache import SpriteCache

    class _CustomSource:
        """Фейковый источник для проверки OCP-регистрации."""
        def frames(self, key, frame_count):
            return ["custom"] * frame_count
        def size(self):
            return (16, 16)
        def supports(self, key):
            return True

    cache = SpriteCache(_FakeAssets(), _FakeCfg())
    cache.register_source("custom", _CustomSource())
    cache.set_default_source("custom")
    assert cache.default_source.__class__.__name__ == "_CustomSource"


def test_sprite_cache_unknown_source_raises():
    from views.sprite_cache import SpriteCache

    cache = SpriteCache(_FakeAssets(), _FakeCfg())
    with pytest.raises(KeyError):
        cache.set_default_source("ghost")