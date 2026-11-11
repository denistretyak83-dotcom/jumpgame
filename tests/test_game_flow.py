"""Тесты CollisionDirector: обработка коллизий в игровые правила (Фаза 3)."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None
from core.event_bus import GameEvents
from core.gameplay import CollisionDirector
from core.state_manager import GameState, StateManager
from models.collision_system import CollisionResult

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
from core.game import Game


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