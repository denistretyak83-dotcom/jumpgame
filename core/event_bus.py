"""EventBus -- Simple event system for decoupling game components.

Allows components to subscribe to specific events and emit signals.
Usage:
    bus = EventBus()
    bus.subscribe('coin_collected', print)
    bus.emit('coin_collected', {'score': 10})
"""
from typing import Dict, List, Callable, Any, Optional

class EventBus:
    def __init__(self):
        # Хранит словарь: событие -> список функций-обработчиков
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, callback: Callable) -> None:
        """Добавляет слушателя для события."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(callback)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Запускает событие, передавая аргументы всем подписчикам."""
        if event in self._handlers:
            for callback in self._handlers[event]:
                callback(*args, **kwargs)

    def clear(self) -> None:
        """Очищает все подписки (полезно при перезапуске игры)."""
        self._handlers.clear()