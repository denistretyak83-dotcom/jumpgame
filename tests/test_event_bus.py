"""Тесты EventBus (core/event_bus.py, без pygame)."""

from core.event_bus import EventBus, GameEvents


def test_subscribe_and_emit():
    bus = EventBus()
    calls = []
    token = bus.subscribe(GameEvents.COIN_COLLECTED, lambda _score: calls.append("hit"))
    bus.emit(GameEvents.COIN_COLLECTED, 5)
    assert calls == ["hit"]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    calls = []
    token = bus.subscribe(GameEvents.COIN_COLLECTED, lambda _s: calls.append("x"))
    bus.unsubscribe(token)
    bus.emit(GameEvents.COIN_COLLECTED, 1)
    assert calls == []


def test_error_isolation_does_not_block_others():
    """Сбой одного подписчика не должен ронять остальных."""
    bus = EventBus()
    ok = []
    bus.subscribe(GameEvents.PLAYER_DIED, lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    bus.subscribe(GameEvents.PLAYER_DIED, lambda: ok.append("survived"))
    bus.emit(GameEvents.PLAYER_DIED)
    assert ok == ["survived"]


def test_gamnevents_constants_are_strings():
    assert GameEvents.PLAYER_JUMP == "player.jump"
    assert isinstance(GameEvents.GAME_OVER, str)
