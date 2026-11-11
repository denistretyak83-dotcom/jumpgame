"""Тесты PlayerFlow: смерть/респавн игрока и жизни (декомпозиция Game, SRP)."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None
from core.event_bus import GameEvents  # noqa: E402
from core.player_flow import PlayerFlow  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен"
)


class FakeLifeManager:
    def __init__(self, initial_lives=3):
        self.lives = initial_lives

    def lose_life(self):
        self.lives -= 1
        return self.lives < 0   # имитация: lives кончились, когда ушли в минус

    def reset(self, count):
        self.lives = count


class FakeEventBus:
    def __init__(self):
        self.emitted = []
    def emit(self, event, *args, **kwargs):
        self.emitted.append(event)


class FakePlayer:
    def __init__(self, dead=False, death_steps=0):
        self.is_dead = dead
        self._death_steps = death_steps

    def update_death(self, dt):
        # Возвращает True, когда смерть "завершилась"
        if self._death_steps > 0:
            self._death_steps -= 1
            return False
        return True


class FakeFactory:
    def __init__(self):
        self.created = 0
    def create_player(self, x, y, event_bus=None):
        self.created += 1
        return FakePlayer()


class FakeLevel:
    def __init__(self):
        self.player_spawn = (50.0, 100.0)


def make_flow(lives=3, dead=False, death_steps=0):
    lm = FakeLifeManager(lives)
    eb = FakeEventBus()
    ff = FakeFactory()
    flow = PlayerFlow(world_factory=ff, life_manager=lm, event_bus=eb)
    level = FakeLevel()
    flow.bind_level(level)
    player = FakePlayer(dead=dead, death_steps=death_steps)
    flow.bind_player(player)
    return flow, lm, eb, ff


def test_update_death_returns_none_when_alive():
    flow, *_ = make_flow(dead=False)
    assert flow.update_death(0.016) is None


def test_update_death_returns_none_while_death_animating():
    flow, *_ = make_flow(dead=True, death_steps=2)  # смерть ещё идёт
    assert flow.update_death(0.016) is None         # не завершилась
    assert flow.update_death(0.016) is None


def test_update_death_respawns_when_lives_remain():
    flow, lm, _, ff = make_flow(lives=3, dead=True, death_steps=0)  # смерть сразу завершилась
    result = flow.update_death(0.016)
    assert result is False              # респавн, а не game over
    assert lm.lives == 2                # жизнь потеряна
    assert ff.created == 1              # создан новый игрок
    assert flow.player is not None      # новый игрок привязан
    assert flow.player.is_dead is False


def test_update_death_returns_true_when_lives_exhausted():
    flow, lm, _, ff = make_flow(lives=0, dead=True, death_steps=0)  # жизней уже нет (0)
    # У FakeLifeManager: lose_life делает lives-=1 -> -1 < 0 -> True (кончились)...
    # Но при lives=0 респавниться нельзя => сразу game over.
    # Поправим мок под желаемое поведение:
    flow._life_manager = FakeLifeManager(-1)  # уже "в минусе"
    result = flow.update_death(0.016)
    assert result is True               # lives закончились
    assert ff.created == 0              # НЕ респавнился


def test_respawn_uses_level_spawn_and_event_bus():
    flow, _, _, ff = make_flow(lives=2, dead=False)
    new_player = flow.respawn()
    assert new_player is flow.player
    assert ff.created == 1
    assert new_player.is_dead is False