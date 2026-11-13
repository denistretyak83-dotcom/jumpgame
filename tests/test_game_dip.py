"""DIP-тесты (шаг 4): Game принимает зависимости через services.

Проверяем:
  - переданные через services реализации подставляются вместо реальных;
  - при инъекции GameOverHandler ему пере-устанавливается колбэк reset_run_state;
  - логические SRP-сервисы (player_flow/level_transition/collision_director)
    имеют дефолтные реальные реализации (без services).

Внешняя среда (окно, рендер, звук, ресурсы, файлы уровней) НЕ создаётся —
подкладываем фейки через services, чтобы тест не зависел от среды/дисков.
"""

import unittest.mock

import pytest

from core.game import Game


# ----------------------------------------------------------------------
# Фейки внешней среды и сервисов
# ----------------------------------------------------------------------
class _Stub:
    def __init__(self, name="stub"):
        self.name = name


class _StubGameOverHandler:
    def __init__(self):
        self.reset_callback = None

    def set_reset_callback(self, callback):
        self.reset_callback = callback


def _fake_services(**overrides):
    """Полный набор подложек для Game(services=...)."""
    base = {
        "screen": _Stub("screen"),
        "sprite_cache": _Stub("sprite_cache"),
        "coin_icon": _Stub("coin_icon"),
        "renderer": _Stub("renderer"),
        "asset_loader": _Stub("assets"),
        "sounds": unittest.mock.MagicMock(),   # нужны методы play_* (attach_audio_listener)
        "world_factory": unittest.mock.MagicMock(),
        "player_flow": _Stub("player_flow"),
        "level_transition": _Stub("level_transition"),
        "collision_director": _Stub("collision_director"),
        "game_over_handler": _StubGameOverHandler(),
    }
    base.update(overrides)
    return base


@pytest.fixture
def fake_services():
    return _fake_services()


def _make_game(**services):
    """Собрать Game с заданными services, не давая __init__ грузить реальный мир.

    reset_run_state замокана: она вызывается в конце __init__ и грузит level_1
    через LevelManager (файлы/мир) — в тестах нам это не нужно.
    """
    with unittest.mock.patch.object(Game, "reset_run_state", lambda self: None):
        return Game(services=services)


# ----------------------------------------------------------------------
# Инъекция
# ----------------------------------------------------------------------
class TestInjection:
    def test_all_services_are_used_when_provided(self, fake_services):
        game = _make_game(**fake_services)

        assert game.screen is fake_services["screen"]
        assert game.sprite_cache is fake_services["sprite_cache"]
        assert game.coin_icon is fake_services["coin_icon"]
        assert game.renderer is fake_services["renderer"]
        assert game.assets is fake_services["asset_loader"]
        assert game.sounds is fake_services["sounds"]
        assert game.world_factory is fake_services["world_factory"]
        assert game.player_flow is fake_services["player_flow"]
        assert game.level_transition is fake_services["level_transition"]
        assert game.collision_director is fake_services["collision_director"]
        assert game.game_over_handler is fake_services["game_over_handler"]

    def test_injected_game_over_handler_gets_reset_callback(self, fake_services):
        goh = fake_services["game_over_handler"]
        _make_game(**fake_services)
        assert goh.reset_callback is not None


# ----------------------------------------------------------------------
# Обратная совместимость: дефолтные логические сервисы
# ----------------------------------------------------------------------
class TestDefaults:
    def test_missing_player_flow_defaults_to_real_class(self):
        # Не передаём player_flow — должен создаться реальный PlayerFlow (дефолт).
        services = _fake_services(player_flow=_Stub("DEFAULT_MARKER"))
        # Если оставить дефолт — это реальный PlayerFlow; мы же проверяем, что без
        # ключа создаётся реальный класс. Для чистоты уберём ключ player_flow вовсе.
        services.pop("player_flow")

        game = _make_game(**services)
        from core.player_flow import PlayerFlow
        assert isinstance(game.player_flow, PlayerFlow)

    def test_missing_level_transition_defaults_to_real_class(self):
        services = _fake_services()
        services.pop("level_transition")
        game = _make_game(**services)
        from core.level_transition import LevelTransition
        assert isinstance(game.level_transition, LevelTransition)

    def test_missing_collision_director_defaults_to_real_class(self):
        services = _fake_services()
        services.pop("collision_director")
        game = _make_game(**services)
        from core.gameplay import CollisionDirector
        assert isinstance(game.collision_director, CollisionDirector)