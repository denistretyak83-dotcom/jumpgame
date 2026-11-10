"""Тесты сервисов состояния: LifeManager, ScoreManager, RespawnService."""
import pytest

from core.event_bus import GameEvents
from core.game_services import LifeManager, ScoreManager, RespawnService


class FakeEventBus:
    def __init__(self):
        self.emitted = []

    def emit(self, event, value=None):
        self.emitted.append((event, value))


# --------------------------------------------------------------------------
# LifeManager
# --------------------------------------------------------------------------
def test_life_manager_initial_lives():
    bus = FakeEventBus()
    lm = LifeManager(initial_lives=3, event_bus=bus)
    assert lm.lives == 3


def test_lose_life_decrements():
    bus = FakeEventBus()
    lm = LifeManager(3, bus)
    assert lm.lose_life() is False   # 2 осталось, не 0
    assert lm.lives == 2


def test_lose_life_to_zero_returns_true():
    bus = FakeEventBus()
    lm = LifeManager(1, bus)
    assert lm.lose_life() is True    # lives <= 0


def test_life_manager_emits_lives_changed():
    bus = FakeEventBus()
    lm = LifeManager(3, bus)
    lm.lose_life()
    assert (GameEvents.LIVES_CHANGED, 2) in bus.emitted


def test_life_manager_reset():
    bus = FakeEventBus()
    lm = LifeManager(3, bus)
    lm.lose_life()
    lm.reset(5)
    assert lm.lives == 5


# --------------------------------------------------------------------------
# ScoreManager
# --------------------------------------------------------------------------
def test_score_manager_start_zero():
    bus = FakeEventBus()
    sm = ScoreManager(bus)
    assert sm.score == 0


def test_add_points_default_one():
    bus = FakeEventBus()
    sm = ScoreManager(bus)
    sm.add_points()
    assert sm.score == 1


def test_add_points_multiple():
    bus = FakeEventBus()
    sm = ScoreManager(bus)
    sm.add_points(5)
    sm.add_points(3)
    assert sm.score == 8


def test_score_manager_emits_score_changed():
    bus = FakeEventBus()
    sm = ScoreManager(bus)
    sm.add_points(10)
    assert (GameEvents.SCORE_CHANGED, 10) in bus.emitted


def test_score_manager_reset():
    bus = FakeEventBus()
    sm = ScoreManager(bus)
    sm.add_points(7)
    sm.reset()
    assert sm.score == 0


# --------------------------------------------------------------------------
# RespawnService
# --------------------------------------------------------------------------
class FakeWorldFactory:
    def __init__(self):
        self.created = []

    def create_player(self, x, y, event_bus):
        p = {"x": x, "y": y}
        self.created.append(p)
        return p


def test_respawn_service_create_player_appends():
    wf = FakeWorldFactory()
    rs = RespawnService(wf)
    entities = []
    rs.bind(entities, (100, 200), object())
    assert len(entities) == 1
    assert rs.player == entities[0]
    assert wf.created[0] == {"x": 100, "y": 200}


def test_respawn_service_replaces_player_in_place():
    wf = FakeWorldFactory()
    rs = RespawnService(wf)
    # имитируем наличие других сущностей до игрока
    ghost1 = "ghost1"
    rs._entities = [ghost1]          # ручная привязка внутреннего списка
    rs.create_player((50, 50), object())
    first = rs.player
    # теперь ещё раз — новый игрок должен ЗАМЕНИТЬ старого в том же списке
    rs.create_player((60, 60), object())
    second = rs.player
    assert rs._entities[1] is second  # заменён по индексу, порядок сохранён
    assert rs._entities[0] is ghost1  # ghost не тронут
    assert first is not second


def test_respawn_service_player_property_none_before_bind():
    wf = FakeWorldFactory()
    rs = RespawnService(wf)
    assert rs.player is None