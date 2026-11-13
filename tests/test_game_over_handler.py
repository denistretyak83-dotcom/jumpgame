"""Unit-тесты для core/game_over_handler.GameOverHandler.

Проверяют ответственность сервиса (SRP, декомпозиция Game):
  - вход в Game Over (start): флаг, событие GAME_OVER, старт фейда;
  - пиксельный фейд (update/_update_fade): наращивание до 255 и остановка;
  - рестарт по R: вызов колбэка reset_run_state и возврат True;
  - сброс состояния (reset).
"""

import pygame
import pytest

from core.game_over_handler import GameOverHandler
from core.event_bus import GameEvents


# ----------------------------------------------------------------------
# Fakes (без зависимости от реального EventBus / StateManager / pygame-окна)
# ----------------------------------------------------------------------
class FakeEventBus:
    """Записывает эмитируемые имена событий."""

    def __init__(self):
        self.events = []

    def emit(self, event_name, *args, **kwargs):
        self.events.append(event_name)


class FakeGameConfig:
    """Минимальный конфиг: нужен только config.game.fade_speed."""

    class _Game:
        fade_speed = 100.0  # условные единицы фейда в секунду

    def __init__(self):
        self.game = self._Game()


@pytest.fixture
def config():
    return FakeGameConfig()


@pytest.fixture
def event_bus():
    return FakeEventBus()


@pytest.fixture
def reset_calls():
    return []


@pytest.fixture
def handler(config, event_bus, reset_calls):
    """GameOverHandler с переданным колбэком-счётчиком рестарта."""
    return GameOverHandler(
        config=config,
        event_bus=event_bus,
        reset_run_state=lambda: reset_calls.append("reset"),
    )


# ----------------------------------------------------------------------
# start() — вход в Game Over
# ----------------------------------------------------------------------
class TestStart:
    def test_start_sets_game_over_flag_and_emits_event(self, handler, event_bus):
        assert handler.game_over is False
        handler.start()
        assert handler.game_over is True
        assert event_bus.events == [GameEvents.GAME_OVER]

    def test_start_begins_fade(self, handler):
        assert handler.fade_level == 0
        assert handler.fade_direction == 0
        handler.start()
        assert handler.fade_direction == 1
        assert handler.fade_level == 0


# ----------------------------------------------------------------------
# update(dt, keys) — фейд
# ----------------------------------------------------------------------
class TestFade:
    def test_update_without_r_advances_fade(self, handler):
        handler.start()
        handler.update(dt=0.1, keys={pygame.K_r: False})
        assert handler.fade_level == pytest.approx(10.0)  # 100 px/s * 0.1 s

    def test_update_returns_false_when_not_restarting(self, handler):
        handler.start()
        result = handler.update(dt=0.1, keys={pygame.K_r: False})
        assert result is False

    def test_fade_clamps_at_255_and_stops(self, handler):
        handler.start()
        # Большой dt — фейд должен упереться в 255 и остановиться.
        handler.update(dt=100.0, keys={pygame.K_r: False})
        assert handler.fade_level == 255
        assert handler.fade_direction == 0

    def test_fade_stays_idle_after_completion(self, handler):
        handler.start()
        handler.update(dt=100.0, keys={pygame.K_r: False})  # -> 255, direction=0
        handler.update(dt=0.1, keys={pygame.K_r: False})
        assert handler.fade_level == 255

    def test_update_when_not_started_does_nothing(self, handler):
        # Без start() фейд не запущен (fade_direction == 0), уровень не растёт.
        handler.update(dt=0.1, keys={pygame.K_r: False})
        assert handler.fade_level == 0


# ----------------------------------------------------------------------
# update(dt, keys) — рестарт по R
# ----------------------------------------------------------------------
class TestRestart:
    def test_restart_on_r_invokes_callback_and_returns_true(
        self, handler, reset_calls
    ):
        handler.start()
        result = handler.update(dt=0.1, keys={pygame.K_r: True})
        assert result is True
        assert reset_calls == ["reset"]

    def test_restart_clears_game_over_and_fade(self, handler, event_bus, reset_calls):
        handler.start()
        handler.update(dt=100.0, keys={pygame.K_r: True})
        # После рестарта сервис полностью сброшен.
        assert handler.game_over is False
        assert handler.fade_level == 0
        assert handler.fade_direction == 0
        # Событие GAME_OVER эмитилось ровно один раз (при start), не при рестарте.
        assert event_bus.events == [GameEvents.GAME_OVER]

    def test_no_restart_callback_when_r_not_pressed(self, handler, reset_calls):
        handler.start()
        handler.update(dt=0.1, keys={pygame.K_r: False})
        assert reset_calls == []


# ----------------------------------------------------------------------
# reset() — ручной сброс
# ----------------------------------------------------------------------
class TestReset:
    def test_reset_clears_all_state(self, handler, event_bus):
        handler.start()
        handler.reset()
        assert handler.game_over is False
        assert handler.fade_level == 0
        assert handler.fade_direction == 0

    def test_reset_does_not_emit_event(self, handler, event_bus):
        handler.start()
        handler.reset()
        # reset() не эмитит событие (это делает только start()).
        assert event_bus.events == [GameEvents.GAME_OVER]