"""Тесты Game: _apply_collisions и _update_game_over_fade (изолировано).

Используем object.__new__(Game), чтобы обойти тяжёлый pygame-конструктор,
и подставляем фейковые зависимости. Это фиксирует текущее поведение
_apply_collisions ДО декомпозиции (пункт 4.7 плана: тесты Game до выноса).
"""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None
from core.game import Game
from core.event_bus import GameEvents
from core.state_manager import StateManager, GameState
from models.collision_system import CollisionResult

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeCfg:
    class GameCfg:
        lives = 3
        fade_speed = 100.0

    game = GameCfg()


class FakeCollision:
    def check(self, *args, **kwargs):
        return CollisionResult()


class FakeScore:
    def __init__(self):
        self.score = 0
    def add_points(self, pts=1):
        self.score += pts


class FakeSounds:
    def play_coin(self): pass
    def play_win(self): pass
    def play_music(self): pass


class FakeEventBus:
    def __init__(self):
        self.emitted = []
    def emit(self, event, *args, **kwargs):
        self.emitted.append(event)


class FakePlayer:
    def __init__(self):
        self.rect = None
        self.is_dead = False
    def die(self, launch_up=True):
        self.is_dead = True


class FakeEnemy:
    def __init__(self):
        self.rect = None
    def spawn_copy(self):
        return self


def make_game(**overrides):
    g = object.__new__(Game)
    g.config = overrides.get('config', FakeCfg())
    g.event_bus = overrides.get('event_bus', FakeEventBus())
    g.state = overrides.get('state', StateManager())
    g.collision_system = overrides.get('collision', FakeCollision())
    g.score_manager = overrides.get('score', FakeScore())
    g.sounds = overrides.get('sounds', FakeSounds())
    g.player = overrides.get('player', FakePlayer())
    g.coins = overrides.get('coins', [])
    g.coin_collected = overrides.get('coin_collected', [])
    g.entities = overrides.get('entities', [])
    g.level = overrides.get('level', None)
    g.won = False
    g.game_over = False
    g.fade_level = 0
    g.fade_direction = 0
    return g


class FakeLevel:
    def __init__(self, flag_rect=None):
        self.flag_rect = flag_rect


# --------------------------------------------------------------------------
# _apply_collisions — монеты
# --------------------------------------------------------------------------
def test_coin_collection_marks_and_scores():
    g = make_game()
    g.coins = [object(), object()]            # 2 монеты
    g.coin_collected = [False, False]
    g.level = FakeLevel()

    class CollThatHitsCoin0:
        def check(self, *a, **k):
            return CollisionResult(coin_index=0)

    g.collision_system = CollThatHitsCoin0()
    g._apply_collisions(0.016)
    assert g.coin_collected[0] is True
    assert g.score_manager.score == 1
    assert GameEvents.COIN_COLLECTED in g.event_bus.emitted


def test_coin_collection_marks_only_that_coin():
    g = make_game()
    g.coins = [object(), object()]
    g.coin_collected = [False, False]
    g.level = FakeLevel()

    class CollThatHitsCoin1:
        def check(self, *a, **k):
            return CollisionResult(coin_index=1)

    g.collision_system = CollThatHitsCoin1()
    g._apply_collisions(0.016)
    assert g.coin_collected == [False, True]


# --------------------------------------------------------------------------
# _apply_collisions — враг
# --------------------------------------------------------------------------
def test_enemy_hit_kills_player():
    g = make_game()
    g.level = FakeLevel()
    enemy = FakeEnemy()

    class CollHitsEnemy:
        def check(self, *a, **k):
            return CollisionResult(hit_enemy=enemy)

    g.collision_system = CollHitsEnemy()
    g._apply_collisions(0.016)
    assert g.player.is_dead is True
    assert GameEvents.PLAYER_DIED in g.event_bus.emitted


# --------------------------------------------------------------------------
# _apply_collisions — флаг (победа)
# --------------------------------------------------------------------------
def test_flag_hit_sets_won_and_state_won():
    g = make_game()
    g.level = FakeLevel()

    class CollHitsFlag:
        def check(self, *a, **k):
            return CollisionResult(hit_flag=True)

    g.collision_system = CollHitsFlag()
    g._apply_collisions(0.016)
    assert g.won is True
    assert g.state.state is GameState.WON
    assert GameEvents.LEVEL_WON in g.event_bus.emitted


# --------------------------------------------------------------------------
# _apply_collisions — падение
# --------------------------------------------------------------------------
def test_fell_out_kills_player():
    g = make_game()
    g.level = FakeLevel()

    class CollFellOut:
        def check(self, *a, **k):
            return CollisionResult(fell_out=True)

    g.collision_system = CollFellOut()
    g._apply_collisions(0.016)
    assert g.player.is_dead is True
    assert GameEvents.PLAYER_DIED in g.event_bus.emitted


# --------------------------------------------------------------------------
# _apply_collisions — нет коллизий (ничего не происходит)
# --------------------------------------------------------------------------
def test_no_collisions_no_side_effects():
    g = make_game()
    g.coins = [object()]
    g.coin_collected = [False]
    g.level = FakeLevel()
    g._apply_collisions(0.016)   # FakeCollision вернёт пустой CollisionResult
    assert g.score_manager.score == 0
    assert g.player.is_dead is False
    assert g.won is False
    assert g.event_bus.emitted == []


# --------------------------------------------------------------------------
# _update_game_over_fade
# --------------------------------------------------------------------------
def test_game_over_fade_increases_up_to_255():
    g = make_game()
    g.fade_direction = 1
    g.fade_level = 0
    g._update_game_over_fade(1.0)          # speed=100 -> +100
    assert g.fade_level == pytest.approx(100.0)


def test_game_over_fade_clamps_at_255_then_stops():
    g = make_game()
    g.fade_direction = 1
    g.fade_level = 250
    g._update_game_over_fade(1.0)          # 250 + 100 = 350 -> clamp 255
    assert g.fade_level == 255
    assert g.fade_direction == 0           # останавливается


def test_game_over_fade_idle_when_direction_zero():
    g = make_game()
    g.fade_direction = 0
    g.fade_level = 50
    g._update_game_over_fade(1.0)
    assert g.fade_level == 50              # не меняется