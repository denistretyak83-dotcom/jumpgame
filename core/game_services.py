"""Выделенные сервисы состояния игры (SRP: каждый отвечает за одно)."""
from typing import Optional
from core.event_bus import GameEvents


class LifeManager:
    def __init__(self, initial_lives: int, event_bus):
        self._lives = initial_lives
        self._event_bus = event_bus

    @property
    def lives(self) -> int:
        return self._lives

    def lose_life(self) -> bool:
        self._lives -= 1
        self._event_bus.emit(GameEvents.LIVES_CHANGED, self._lives)
        return self._lives <= 0

    def reset(self, initial_lives: int) -> None:
        self._lives = initial_lives


class ScoreManager:
    def __init__(self, event_bus):
        self._score = 0
        self._event_bus = event_bus

    @property
    def score(self) -> int:
        return self._score

    def add_points(self, points: int = 1) -> None:
        self._score += points
        self._event_bus.emit(GameEvents.SCORE_CHANGED, self._score)

    def reset(self) -> None:
        self._score = 0


class RespawnService:
    """Создание и замена игрока при респауне / рестарте.

    ВАЖНО: заменяет игрока ВНУТРИ списка сущностей мира по ссылке,
    сохраняя порядок (чтобы коллизии/рендер продолжали работать корректно).
    """

    def __init__(self, world_factory):
        self._world_factory = world_factory
        self._player: Optional[object] = None
        self._entities: Optional[list] = None

    def bind(self, entities: list, spawn, event_bus) -> None:
        """Привязывает список сущностей и создаёт первого игрока."""
        self._entities = entities
        self.create_player(spawn, event_bus)

    def create_player(self, spawn, event_bus) -> None:
        """Создаёт нового игрока и добавляет в список сущностей."""
        player = self._world_factory.create_player(spawn[0], spawn[1], event_bus)
        if self._player is not None and self._entities is not None:
            # заменяем старого игрока, сохраняя позицию
            for i, e in enumerate(self._entities):
                if e is self._player:
                    self._entities[i] = player
                    break
        elif self._entities is not None:
            self._entities.append(player)
        self._player = player

    @property
    def player(self):
        return self._player