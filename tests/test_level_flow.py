"""Тесты LevelFlow: сборка мира из уровня (декомпозиция Game, Фаза 3)."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None
from core.level_flow import LevelFlow  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


class FakeLevelData:
    def __init__(self, coins=2, enemies=2):
        import pygame
        self.name = "level_1"
        self.next_level = None
        self.player_spawn = (100, 200)
        self.platforms = [object()]
        self.coins = [pygame.Rect(i, 0, 16, 16) for i in range(coins)]
        self.enemies = [self._mk_enemy() for _ in range(enemies)]
        self.flag_rect = object()

    @staticmethod
    def _mk_enemy():
        class Enemy:
            def spawn_copy(self):
                return "copy"

        return Enemy()


class FakeLevelManager:
    def __init__(self, level_data):
        self.level_data = level_data

    def load_level(self, name):
        return self.level_data


class _FakePlayer:
    def __init__(self, rect):
        self.rect = rect


class FakeWorldFactory:
    def create_player(self, x, y, event_bus=None):
        import pygame
        return _FakePlayer(pygame.Rect(x, y, 32, 48))


class FakeRenderer:
    def __init__(self):
        self.platforms = None

    def set_platforms(self, platforms):
        self.platforms = platforms


class FakeCamera:
    def __init__(self):
        self.x = None

    def update(self, x):
        self.x = x


class FakeSounds:
    def __init__(self):
        self.music = 0

    def play_music(self):
        self.music += 1


def make_flow(level_data=None):
    ldata = level_data or FakeLevelData(coins=2, enemies=2)
    flow = LevelFlow(
        level_manager=FakeLevelManager(ldata),
        world_factory=FakeWorldFactory(),
        event_bus=object(),
        renderer=FakeRenderer(),
        camera=FakeCamera(),
        sounds=FakeSounds(),
    )
    return flow, ldata


def test_load_and_setup_builds_world():
    flow, ldata = make_flow()
    result = flow.load_and_setup("level_1")
    assert result is ldata
    assert flow.level is ldata
    # игрок создан через фабрику с корректным спавном
    assert flow.player.rect.x == 100
    assert flow.player.rect.y == 200
    # сущности = игрок + враги (spawn_copy)
    assert len(flow.entities) == 1 + len(ldata.enemies)
    assert flow.entities[0] is flow.player
    # монеты скопированы
    assert len(flow.coins) == len(ldata.coins)
    assert len(flow.coin_collected) == len(ldata.coins)
    assert all(v is False for v in flow.coin_collected)


def test_load_and_setup_sets_platforms_in_renderer():
    flow, ldata = make_flow()
    flow.load_and_setup("level_1")
    assert flow.renderer.platforms == ldata.platforms


def test_load_and_setup_updates_camera_and_music():
    flow, _ = make_flow()
    flow.load_and_setup("level_1")
    # камера получила x игрока (100)
    assert flow.camera.x == 100
    assert flow.sounds.music == 1


def test_load_and_setup_entities_are_spawn_copies():
    flow, ldata = make_flow(FakeLevelData(coins=2, enemies=2))
    flow.load_and_setup("level_1")
    # враги после игрока — это spawn_copy() (возвращают "copy")
    copies = [e for e in flow.entities[1:]]
    assert copies == ["copy", "copy"]


def test_no_coins_means_empty_lists():
    flow, _ = make_flow(FakeLevelData(coins=0, enemies=0))
    flow.load_and_setup("level_1")
    assert flow.coins == []
    assert flow.coin_collected == []
    # сущности = только игрок
    assert len(flow.entities) == 1