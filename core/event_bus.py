"""EventBus -- событийная шина для слабой связанности (Observer).

- subscribe() возвращает ТОКЕН для unsubscribe — предотвращает утечку памяти.
- emit() изолирует исключения: сбой одного подписчика не роняет остальных.
- Имена событий вынесены в GameEvents (защита от опечаток).

Usage:
    bus = EventBus()
    token = bus.subscribe(GameEvents.COIN_COLLECTED, handler)
    ...
    bus.unsubscribe(token)         # при уничтожении подписчика
    bus.emit(GameEvents.COIN_COLLECTED, score)
"""
from typing import Callable, Dict, List, Optional, Tuple
import itertools
import logging

logger = logging.getLogger(__name__)

# Монотонный счётчик токенов. НЕ используем id(callback): адреса в Python
# переиспользуются после сборки мусора, что даёт ложные unsubscribe.
_token_counter = itertools.count()


class EventBus:
    """Событийная шина с токенизированной подпиской и изоляцией ошибок."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._tokens: Dict[int, Tuple[str, Callable]] = {}

    # ------------------------------------------------------------------
    # Подписка
    # ------------------------------------------------------------------

    def subscribe(self, event: str, callback: Callable) -> int:
        """Подписывает обработчик на событие. Возвращает token для unsubscribe."""
        self._handlers.setdefault(event, []).append(callback)
        token = next(_token_counter)          # гарантированно уникальный
        self._tokens[token] = (event, callback)
        return token

    def unsubscribe(self, token: Optional[int]) -> None:
        """Отписывает обработчик по токену. Безопасен для повторных вызовов."""
        if token is None or token not in self._tokens:
            return
        event, callback = self._tokens.pop(token)
        try:
            self._handlers[event].remove(callback)
        except (KeyError, ValueError):
            pass  # обработчик уже удалён — не критично

    # ------------------------------------------------------------------
    # Эмиссия
    # ------------------------------------------------------------------

    def emit(self, event: str, *args, **kwargs) -> None:
        """Запускает событие. Ошибка одного подписчика не прерывает остальных."""
        # list(...) — копия, чтобы unsubscribe/удобавление во время emit не ломалось
        for callback in list(self._handlers.get(event, ())):
            try:
                callback(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 — изоляция подписчиков
                logger.exception("Handler for '%s' failed: %s", event, exc)

    # ------------------------------------------------------------------
    # Очистка
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Полная очистка (при перезапуске игры)."""
        self._handlers.clear()
        self._tokens.clear()


# ---------------------------------------------------------------------------
# Центральный реестр имён событий (защита от опечаток и единый источник)
# ---------------------------------------------------------------------------
class GameEvents:
    """Константы событий. Использовать вместо строковых литералов."""

    SCORE_CHANGED = "score_changed"
    LIVES_CHANGED = "lives_changed"
    GAME_OVER = "game_over"
    LEVEL_WON = "level_won"
    COIN_COLLECTED = "coin_collected"
    PLAYER_DIED = "player_died"
    PLAYER_JUMP = "player.jump"
    PLAYER_BUMP = "player.bump"
    CHARACTER_DEATH = "character.death"