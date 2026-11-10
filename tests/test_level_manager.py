"""Тесты LevelBuilder и LevelManager: загрузка/построение уровней из JSON."""
import json
import pathlib
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from levels.level_manager import LevelBuilder, LevelManager  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужны прагмы Rect/фабрики)"
)


def good_factories():
    """Набор фейков-фабрик, возвращающих простые прокси объектов."""
    return {
        "platform": lambda data: ("platform", data),
        "coin": lambda data: ("coin", data),
        "flag": lambda data: ("flag", data),
        "enemy": lambda data: ("enemy", data),
    }


def sample_raw(**overrides):
    raw = {
        "name": "level_1",
        "next_level": "level_2",
        "player_spawn": {"x": 100, "y": 200},
        "platforms": [{"x": 0, "y": 300}],
        "coins": [{"x": 10, "y": 20}],
        "flag": {"x": 500, "y": 100},
        "enemies": [{"behavior": "walker"}],
    }
    raw.update(overrides)
    return raw


# --------------------------------------------------------------------------
# LevelBuilder
# --------------------------------------------------------------------------
def test_builder_creates_level_data():
    builder = LevelBuilder(good_factories())
    data = builder.build(sample_raw())
    assert data.name == "level_1"
    assert data.next_level == "level_2"
    assert data.player_spawn == (100.0, 200.0)
    assert len(data.platforms) == 1
    assert len(data.coins) == 1
    assert len(data.enemies) == 1
    assert data.flag_rect == ("flag", {"x": 500, "y": 100})


def test_builder_missing_keys_raises():
    builder = LevelBuilder(good_factories())
    raw = sample_raw()
    del raw["flag"]   # обязательный ключ
    with pytest.raises(ValueError):
        builder.build(raw)


def test_builder_defaults_for_optional_fields():
    builder = LevelBuilder(good_factories())
    raw = sample_raw()
    raw.pop("next_level", None)   # next_level опционален
    raw.pop("enemies", None)      # enemies опционален (raw.get)
    data = builder.build(raw)
    assert data.next_level is None
    assert data.enemies == []
    # coins ОБЯЗАТЕЛЬНЫ в билдере (raw["coins"]) — они остаются
    assert data.coins == [("coin", {"x": 10, "y": 20})]


def test_builder_default_name_unknown():
    builder = LevelBuilder(good_factories())
    raw = sample_raw()
    raw.pop("name", None)
    data = builder.build(raw)
    assert data.name == "unknown"


def test_builder_passes_data_to_factories():
    builder = LevelBuilder(good_factories())
    data = builder.build(sample_raw())
    # фабрика platform получила сырые данные платформы
    assert data.platforms[0] == ("platform", {"x": 0, "y": 300})
    # фабрика enemy получила данные врага
    assert data.enemies[0] == ("enemy", {"behavior": "walker"})


# --------------------------------------------------------------------------
# LevelManager
# --------------------------------------------------------------------------
@pytest.fixture
def make_manager(tmp_path):
    def _mgr():
        levels = tmp_path / "levels"
        levels.mkdir(exist_ok=True)
        return LevelManager(tmp_path, good_factories())
    return _mgr


def write_level(tmp_path, name, content):
    levels = tmp_path / "levels"
    levels.mkdir(exist_ok=True)
    (levels / name).write_text(json.dumps(content), encoding="utf-8")


def test_load_level_from_json(tmp_path):
    write_level(tmp_path, "test.json", sample_raw())
    mgr = LevelManager(tmp_path, good_factories())
    data = mgr.load_level("test")
    assert data.name == "level_1"


def test_load_level_adds_json_extension(tmp_path):
    # без .json в имени
    write_level(tmp_path, "a.json", sample_raw())
    mgr = LevelManager(tmp_path, good_factories())
    data = mgr.load_level("a")
    assert data.name == "level_1"


def test_load_level_missing_file_raises(tmp_path):
    mgr = LevelManager(tmp_path, good_factories())
    with pytest.raises(FileNotFoundError):
        mgr.load_level("nope")


def test_load_level_caches_result(tmp_path):
    write_level(tmp_path, "c.json", sample_raw())
    mgr = LevelManager(tmp_path, good_factories())
    d1 = mgr.load_level("c")
    d2 = mgr.load_level("c")
    assert d1 is d2    # один объект из кеша


def test_invalid_json_raises_runtime_error(tmp_path):
    levels = tmp_path / "levels"
    levels.mkdir(exist_ok=True)
    (levels / "bad.json").write_text("{ not valid json", encoding="utf-8")
    mgr = LevelManager(tmp_path, good_factories())
    with pytest.raises(RuntimeError):
        mgr.load_level("bad")


def test_clear_cache_specific_and_all(tmp_path):
    write_level(tmp_path, "x.json", sample_raw())
    mgr = LevelManager(tmp_path, good_factories())
    mgr.load_level("x")          # заполнили кеш
    assert "x" in mgr._cache
    mgr.clear_cache("x")
    assert "x" not in mgr._cache
    # снова загружаем и чистим всё
    mgr.load_level("x")
    assert mgr._cache
    mgr.clear_cache()
    assert not mgr._cache