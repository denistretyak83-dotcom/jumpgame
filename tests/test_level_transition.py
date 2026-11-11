"""Тесты LevelTransition: каталог/переходы по next_level (SRP)."""
import pytest

from core.level_transition import LevelTransition


class FakeLevelData:
    """Имитация возврата реального LevelManager.load_level."""
    def __init__(self, name, next_level):
        self.name = name
        self.next_level = next_level


class RealisticFakeLevelManager:
    """Мак реального LevelManager: load_level -> LevelData, next_level_name -> str|None."""
    def __init__(self, mapping):
        self._mapping = mapping  # {name: next_name_or_None}

    def load_level(self, name):
        return FakeLevelData(name, self._mapping.get(name))

    def next_level_name(self, name):
        return self.load_level(name).next_level


class FakeLevelFlow:
    """Имитация LevelFlow: load_and_setup выставляет ВСЕ атрибуты мира."""
    def __init__(self):
        self.loaded = []

    def load_and_setup(self, name):
        self.loaded.append(name)
        self.level = {"name": name}
        self.player = "player:" + name
        self.entities = [object()]
        self.coins = [object()]
        self.coin_collected = [False]


def make_transition(mapping):
    lm = RealisticFakeLevelManager(mapping)
    flow = FakeLevelFlow()
    return LevelTransition(level_manager=lm, level_flow=flow), flow


def test_load_level_sets_current_and_returns_world():
    tr, flow = make_transition({"level_1": "level_2", "level_2": None})
    world = tr.load_level("level_1")
    assert world["level"] == {"name": "level_1"}
    assert world["player"] == "player:level_1"
    assert tr.current_level_name == "level_1"
    assert flow.loaded == ["level_1"]


def test_advance_to_next_level_returns_next_world():
    tr, flow = make_transition({"level_1": "level_2", "level_2": None})
    tr.load_level("level_1")
    world = tr.advance_to_next_level()
    assert world is not None
    assert tr.current_level_name == "level_2"
    assert world["player"] == "player:level_2"


def test_advance_returns_none_on_last_level():
    tr, flow = make_transition({"level_1": "level_2", "level_2": None})
    tr.load_level("level_2")
    assert tr.advance_to_next_level() is None
    assert tr.current_level_name == "level_2"


def test_restart_first_loads_level_1():
    tr, flow = make_transition({"level_1": "level_2", "level_2": None})
    tr.load_level("level_2")
    world = tr.restart_first()
    assert tr.current_level_name == "level_1"
    assert world["player"] == "player:level_1"


def test_has_next_level():
    tr, _ = make_transition({"level_1": "level_2", "level_2": None})
    tr.load_level("level_1")
    assert tr.has_next_level() is True
    tr.load_level("level_2")
    assert tr.has_next_level() is False