"""ФР-2: ProceduralPixelArt — генератор спрайтов из ASCII-карт и фигур."""

import importlib.util

import pytest

# Мокаем pygame мы будем осторожно: создание Surface без дисплея ок,
# но операции draw в CI должны идти без реального окна. Используем dummy.


def _have_pygame() -> bool:
    return importlib.util.find_spec("pygame") is not None


@pytest.fixture
def procedural():
    if not _have_pygame():
        pytest.skip("pygame недоступен")
    from views.sprites.procedural import ProceduralSpriteSource

    class _FakeCfg:
        pass

    return ProceduralSpriteSource(_FakeCfg(), scale=2)


def test_procedural_is_sprite_source(procedural):
    from views.sprites.sprite_source import SpriteSource

    assert isinstance(procedural, SpriteSource) is True


def test_procedural_supports_keys(procedural):
    assert procedural.supports("player_idle") is True
    assert procedural.supports("player_jump") is True
    assert procedural.supports("enemy_walk") is True
    assert procedural.supports("coin") is True
    assert procedural.supports("tile") is True
    assert procedural.supports("nonexistent") is False


def test_procedural_player_frames_have_size(procedural):
    frames = procedural.frames("player_idle", 3)
    assert len(frames) >= 1
    # размер карты героя 8x10 * scale 2 = 16x20
    assert frames[0].get_size() == (16, 20)


def test_procedural_coin_frames(procedural):
    frames = procedural.frames("coin", 1)
    assert len(frames) == 1
    assert frames[0].get_size() == (32, 32)  # 16*2


def test_procedural_tile_frames(procedural):
    frames = procedural.frames("tile", 1)
    assert len(frames) == 1
    assert frames[0].get_size() == (64, 64)  # 32*2


def test_procedural_unknown_key_raises(procedural):
    with pytest.raises(KeyError):
        procedural.frames("ghost", 1)


def test_sprite_cache_can_use_procedural_source():
    if not _have_pygame():
        pytest.skip("pygame недоступен")
    from views.sprites.procedural import ProceduralSpriteSource
    from views.sprite_cache import SpriteCache

    class _FakeAssets:
        def load_animation_frames(self, folder, count, scale):
            return ["frame"] * count

    class _FakeCfg:
        class _anim:
            idle_delay = 0.1
            run_delay = 0.1
            walk_delay = 0.15
            jump_delay = 0.13
        animation = _anim()

        class _player:
            width = 16
            height = 20
        player = _player()

    cache = SpriteCache(_FakeAssets(), _FakeCfg())
    cache.register_source("procedural", ProceduralSpriteSource(_FakeCfg(), scale=2))
    cache.set_default_source("procedural")
    view = cache.player_view()
    assert view is not None