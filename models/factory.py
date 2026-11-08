# models/factory.py
"""WorldFactory -- единая реестр-фабрика объектов мира (registry pattern).

Превращает объект уровня (dict из JSON) в инстанс модели. Точка расширения
(OCP): новые типы добавляются через register() без правки существующего
кода. Абстрагирует LevelManager от конкретных классов (DIP).
"""
from typing import Any, Callable, Dict

import pygame

from models.player import Player
from models.enemy import Enemy
from core.config import Settings

# протокол фабрики одного объекта
ObjectFactory = Callable[[dict], Any]


class WorldFactory:
    """Единая фабрика объектов мира (data-driven + registry по OCP)."""

    def __init__(self, asset_loader, config=None, registry=None):
        self.assets = asset_loader
        self.config = config or Settings()
        # Внутренний реестр "тип -> фабрика"
        self._registry: Dict[str, ObjectFactory] = registry or {}
        self._register_defaults()

    # ------------------------------------------------------------------
    # Реестр (OCP)
    # ------------------------------------------------------------------

    def register(self, obj_type: str, factory: ObjectFactory) -> None:
        """OCP: добавить фабрику для нового типа объекта."""
        self._registry[obj_type] = factory

    def create(self, obj_type: str, data: dict) -> Any:
        """Создать объект нужного типа из данных уровня (data-driven)."""
        factory = self._registry.get(obj_type)
        if factory is None:
            known = ", ".join(sorted(self._registry))
            raise KeyError(
                f"WorldFactory: неизвестный тип объекта '{obj_type}'. "
                f"Зарегистрирован: {known}. Используйте register() для OCP."
            )
        return factory(data)

    def entity_factories(self) -> Dict[str, ObjectFactory]:
        """Вернуть dict фабрик для LevelManager (единообразные обёртки)."""
        return {
            obj_type: (lambda d, t=obj_type: self.create(t, d))
            for obj_type in list(self._registry)
        }

    # ------------------------------------------------------------------
    # Дефолтные фабрики (обязательны для работы игры)
    # ------------------------------------------------------------------

    def _register_defaults(self) -> None:
        """Зарегистрировать встроенные типы."""
        self.register("platform", lambda d: self._build_rect(d, name="platform"))
        self.register("coin", lambda d: self._build_rect(d, name="coin"))
        self.register("flag", lambda d: self._build_rect(d, name="flag"))
        self.register("enemy", lambda d: self.create_enemy(d))

    def _build_rect(self, data: dict, name: str) -> pygame.Rect:
        """Построить pygame.Rect из пагины уровня с валидацией ключей."""
        try:
            x = int(data["x"])
            y = int(data["y"])
            w = int(data["w"])
            h = int(data["h"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"{name}: отсутствуют/невалидны ключи прямоугольника "
                f"(нужны x,y,w,h как числа), получено: {data}"
            ) from exc
        return pygame.Rect(x, y, w, h)

    # ------------------------------------------------------------------
    # Фабрики конкретных моделей
    # ------------------------------------------------------------------

    def create_enemy(self, data: dict) -> Enemy:
        """Строит врага из данных уровня (без animations -- теперь View)."""
        return Enemy(
            x=data["x"],
            y=data["y"],
            left=data["left"],
            right=data["right"],
            config=self.config,
            enemy_data=data,
        )


    def create_player(self, x, y, event_bus=None) -> Player:
        """Build Player with spawn coords. event_bus для эмита событий."""
        return Player(x, y, config=self.config, event_bus=event_bus)