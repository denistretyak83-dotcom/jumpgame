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

# --------------------------------------------------------------------------
# Дополнения: unsubscribe-крайние случаи, подписка возвращает токен, clear()
# --------------------------------------------------------------------------
def test_subscribe_returns_unique_tokens():
    bus = EventBus()
    t1 = bus.subscribe("evt", lambda: None)
    t2 = bus.subscribe("evt", lambda: None)
    assert t1 != t2


def test_unsubscribe_with_none_is_safe():
    bus = EventBus()
    bus.unsubscribe(None)   # не должно падать


def test_unsubscribe_unknown_token_is_safe():
    bus = EventBus()
    bus.unsubscribe(999999)  # не существует — безопасно


def test_unsubscribe_twice_is_safe():
    bus = EventBus()
    calls = []
    bus.subscribe("evt", lambda: calls.append(1))
    token = next(iter(bus._tokens.keys()))  # берём единственный токен
    bus.unsubscribe(token)
    bus.unsubscribe(token)   # повторный вызов — не должен падать
    bus.emit("evt")
    assert calls == []


def test_emit_passes_multiple_args_and_kwargs():
    bus = EventBus()
    captured = {}
    def handler(a, b, *, c=0):
        captured['a'] = a
        captured['b'] = b
        captured['c'] = c
    bus.subscribe("evt", handler)
    bus.emit("evt", 1, 2, c=3)
    assert captured == {'a': 1, 'b': 2, 'c': 3}


def test_clear_removes_all_handlers():
    bus = EventBus()
    calls = []
    bus.subscribe("a", lambda: calls.append('a'))
    bus.subscribe("b", lambda: calls.append('b'))
    bus.clear()
    bus.emit("a")
    bus.emit("b")
    assert calls == []


def test_emission_continues_after_handler_error():
    bus = EventBus()
    calls = []

    def broken():
        raise RuntimeError("boom")

    def ok():
        calls.append('ok')

    bus.subscribe("evt", broken)
    bus.subscribe("evt", ok)
    # ошибка первого не прерывает второго
    bus.emit("evt")
    assert calls == ['ok']