"""Тесты CollisionDirector: обработка коллизий в игровые правила (Фаза 3)."""
import collections
import importlib.util
import unittest.mock

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None
try:
    import pygame  # noqa: E402,F401
except ImportError:  # pragma: no cover
    pygame = None

from core.event_bus import GameEvents  # noqa: E402
from core.game import Game  # noqa: E402
from core.gameplay import CollisionDirector  # noqa: E402
from core.state_manager import GameState, StateManager  # noqa: E402
from models.collision_system import CollisionResult  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeScore:
    def __init__(self):
        self.score = 0

    def add_points(self, pts=1):
        self.score += pts


class FakeSounds:
    def __init__(self):
        self.coin = 0
        self.win = 0

    def play_coin(self):
        self.coin += 1

    def play_win(self):
        self.win += 1


class FakeEventBus:
    def __init__(self):
        self.emitted = []

    def emit(self, event, *args, **kwargs):
        self.emitted.append(event)


class FakePlayer:
    def __init__(self):
        self.is_dead = False
        self.rect = None   # rect нужен: process вызывает player.rect

    def die(self, launch_up=True):
        self.is_dead = True

class FakeCollision:
    def __init__(self, result=None):
        self.result = result or CollisionResult()

    def check(self, *a, **k):
        return self.result


class FakeLevel:
    def __init__(self, flag_rect=None):
        self.flag_rect = flag_rect


def make_director(result=None):
    state = StateManager()
    director = CollisionDirector(
        collision_system=FakeCollision(result),
        score_manager=FakeScore(),
        event_bus=FakeEventBus(),
        sounds=FakeSounds(),
        state=state,
    )
    return director


def test_coin_collection_marks_and_scores():
    director = make_director(CollisionResult(coin_index=0))
    coins = [object(), object()]
    coin_collected = [False, False]
    director.process(FakePlayer(), coins, coin_collected, [], None)
    assert coin_collected[0] is True
    assert director.score_manager.score == 1
    assert GameEvents.COIN_COLLECTED in director.event_bus.emitted


def test_coin_collection_marks_only_that_coin():
    director = make_director(CollisionResult(coin_index=1))
    coins = [object(), object()]
    coin_collected = [False, False]
    director.process(FakePlayer(), coins, coin_collected, [], None)
    assert coin_collected == [False, True]


def test_enemy_hit_kills_player():
    director = make_director(CollisionResult(hit_enemy=object()))
    player = FakePlayer()
    director.process(player, [], [], [object()], None)
    assert player.is_dead is True
    assert GameEvents.PLAYER_DIED in director.event_bus.emitted


def test_flag_hit_sets_won_and_state():
    director = make_director(CollisionResult(hit_flag=True))
    director.process(FakePlayer(), [], [], [], object())
    assert director.won is True
    assert director.state.state is GameState.WON
    assert GameEvents.LEVEL_WON in director.event_bus.emitted


def test_fell_out_kills_player():
    director = make_director(CollisionResult(fell_out=True))
    player = FakePlayer()
    director.process(player, [], [], [], None)
    assert player.is_dead is True
    assert GameEvents.PLAYER_DIED in director.event_bus.emitted


def test_no_collisions_no_side_effects():
    director = make_director()  # пустой CollisionResult
    player = FakePlayer()
    coins = [object()]
    coin_collected = [False]
    director.process(player, coins, coin_collected, [], None)
    assert director.score_manager.score == 0
    assert player.is_dead is False
    assert director.won is False
    assert director.event_bus.emitted == []


def test_process_uses_collision_system_with_correct_args():
    # Проверяем, что player исключается из списка врагов
    called = {}

    class RecordingCollision:
        def check(self, player_rect, coins, coin_collected, enemies, flag_rect):
            called['enemies'] = enemies
            return CollisionResult()

    player = FakePlayer()
    director = CollisionDirector(
        collision_system=RecordingCollision(),
        score_manager=FakeScore(),
        event_bus=FakeEventBus(),
        sounds=FakeSounds(),
        state=StateManager(),
    )
    enemy = object()
    director.process(player, [], [], [player, enemy], None)
    # player не передаётся как враг (исключается)
    assert player not in called['enemies']
    assert enemy in called['enemies']


# --------------------------------------------------------------------------
# Тесты на Game._update_game_over_fade (метод остался в Game)
# --------------------------------------------------------------------------
def _make_game_fade():
    g = object.__new__(Game)
    g.fade_direction = 1
    g.fade_level = 0

    class FakeCfg:
        class GameCfg:
            fade_speed = 100.0
        game = GameCfg()
    g.config = FakeCfg()
    return g


def test_game_over_fade_increases():
    g = _make_game_fade()
    g._update_game_over_fade(1.0)
    assert g.fade_level == pytest.approx(100.0)


def test_game_over_fade_clamps_at_255():
    g = _make_game_fade()
    g.fade_level = 250
    g._update_game_over_fade(1.0)
    assert g.fade_level == 255
    assert g.fade_direction == 0


def test_game_over_fade_idle_when_direction_zero():
    g = _make_game_fade()
    g.fade_direction = 0
    g.fade_level = 50
    g._update_game_over_fade(1.0)
    assert g.fade_level == 50


# --------------------------------------------------------------------------
# Переход на следующий уровень (J2) + рестарт после победы на последнем уровне
# --------------------------------------------------------------------------
class _FakeLevelManager:
    """Имитация LevelManager.next_level_name."""

    def __init__(self, next_for_first):
        self._next = next_for_first

    def next_level_name(self, level_name):
        return self._next


class _FakeStateManager:
    """Имитация StateManager (has_ended / set / current)."""

    def __init__(self, initial):
        self.current = initial

    def set(self, new_state):
        self.current = new_state

    def has_ended(self):
        return self.current in (GameState.WON, GameState.GAME_OVER)

    def is_playing(self):
        return self.current is GameState.PLAYING


def _pressed(*keys):
    """Возвращает объект, имитирующий pygame.key.get_pressed()."""
    pressed = collections.defaultdict(bool)
    for k in keys:
        pressed[k] = True
    return pressed


def _run_update(g, pressed_keys=()):
    with unittest.mock.patch.object(pygame.key, "get_pressed", return_value=_pressed(*pressed_keys)):
        g._update(0.016)


def _make_game_for_won():
    g = object.__new__(Game)
    g.current_level_name = "level_2"
    g.won = True
    g.game_over = False
    g.collision_director = type("CD", (), {"won": True})()
    g.level_manager = _FakeLevelManager(None)  # нет следующего уровня
    g.state = _FakeStateManager(GameState.WON)

    # НОВОЕ: заглушка LevelTransition (Game теперь использует self.level_transition)
    g.level_transition = _FakeLevelTransition(next_name=None)  # последний уровень

    g._load_level_calls = []
    g._load_level = lambda name: g._load_level_calls.append(name)
    g.reset_calls = []

    def _reset():
        g.reset_calls.append("reset")
        g.state.current = GameState.PLAYING

    g.reset_run_state = _reset
    return g


def test_won_on_last_level_no_r_stays_on_win_screen():
    g = _make_game_for_won()
    g._advance_to_next_level = lambda: False  # последний уровень (level_2)
    _run_update(g)  # R не нажат
    assert g.reset_calls == []            # не рестартуем
    assert g.state.current is GameState.WON  # остаёмся на экране победы


def test_won_on_last_level_r_restarts():
    g = _make_game_for_won()
    g._advance_to_next_level = lambda: False  # последний уровень (level_2)
    _run_update(g, pressed_keys=(pygame.K_r,))  # R нажат
    assert g.reset_calls == ["reset"]      # рестарт выполнен
    assert g.state.current is not GameState.WON  # состояние переключено reset'ом


def test_won_with_next_level_advances_not_restart():
    # Уровень НЕ последний: переходим дальше, R не проверяется.
    g = _make_game_for_won()
    advanced = []

    def _advance():
        advanced.append(True)
        return True

    g._advance_to_next_level = _advance
    # даже если R нажат, переход происходит раньше
    _run_update(g, pressed_keys=(pygame.K_r,))
    assert advanced == [True]
    assert g.reset_calls == []


def test_advance_to_next_level_loads_next_and_plays():
    g = object.__new__(Game)
    g.current_level_name = "level_1"
    g.level_manager = _FakeLevelManager("level_2")
    g.state = _FakeStateManager(GameState.WON)
    g.loaded = []
    g.won = True
    g.game_over = False
    g.collision_director = type("CD", (), {"won": True})()

    # НОВОЕ: заглушка LevelTransition, переход на level_2
    g.level_transition = _FakeLevelTransition(next_name="level_2")

    # Заменяем _apply_world, чтобы перехватить и не обращаться к player_flow
    def fake_apply(world):
        g.loaded.append(world["level"])

    g._apply_world = fake_apply

    res = g._advance_to_next_level()
    assert res is True
    assert g.loaded  # мир следующего уровня применён
    assert g.state.current is GameState.PLAYING


def test_advance_to_next_level_none_is_last_level():
    g = object.__new__(Game)
    g.current_level_name = "level_2"
    g.level_manager = _FakeLevelManager(None)
    g.state = _FakeStateManager(GameState.WON)
    g.loaded = []
    g.won = True
    g.game_over = False
    g.collision_director = type("CD", (), {"won": True})()

    # НОВОЕ: заглушка LevelTransition, следующего уровня нет
    g.level_transition = _FakeLevelTransition(next_name=None)

    res = g._advance_to_next_level()
    assert res is False
    assert g.loaded == []
    assert g.state.current is GameState.WON


def test_load_level_resets_won_flags_and_coins():
    g = object.__new__(Game)
    g.current_level_name = "level_1"
    g.won = True
    g.game_over = True
    g.collision_director = type("CD", (), {"won": True})()

    # Заглушка PlayerFlow
    g.player_flow = type("PlayerFlowStub", (), {
        "bind_level": lambda self, level: None,
        "bind_player": lambda self, p: None,
    })()

    class FakeLevelFlow:
        def load_and_setup(self, name):
            self.level = object()
            self.player = object()
            self.entities = [object()]
            self.coins = [object(), object()]
            self.coin_collected = [False, False]

    g.level_flow = FakeLevelFlow()

    # Заглушка LevelTransition: load_level(name) эмулирует реальный сервис —
    # вызывает load_and_setup, затем собирает мир.
    class LevelTransitionStub:
        current_level_name = "level_1"
        def load_level(self, name):
            g.level_flow.load_and_setup(name)   # установить атрибуты мира
            return {
                "level": g.level_flow.level,
                "player": g.level_flow.player,
                "entities": g.level_flow.entities,
                "coins": g.level_flow.coins,
                "coin_collected": g.level_flow.coin_collected,
            }

    g.level_transition = LevelTransitionStub()

    g._load_level("level_1")
    assert g.won is False
    assert g.game_over is False
    assert g.collision_director.won is False
    assert g.coin_collected == [False, False]
    assert g.current_level_name == "level_1"

class _FakeLevelTransition:
    """Заглушка LevelTransition для Game-тестов через object.__new__(Game).

    Позволяет _update/_load_level/_advance_to_next_level работать без
    реального сервиса. Через поле `next` управляем, переходить ли на
    следующий уровень.
    """

    def __init__(self, next_name="level_2"):
        self.current_level_name = "level_1"
        self.next = next_name
        self.loaded = []           # фиксируем вызовы load_level

    def load_level(self, name):
        self.loaded.append(name)
        self.current_level_name = name
        return {
            "level": object(),
            "player": object(),
            "entities": [object()],
            "coins": [object()],
            "coin_collected": [False],
        }

    def advance_to_next_level(self):
        if self.next is None:
            return None
        name = self.next
        self.next = None  # после перехода следующих больше нет (как для последнего)
        return self.load_level(name)

    def has_next_level(self):
        return self.next is not None

    def restart_first(self):
        return self.load_level("level_1")