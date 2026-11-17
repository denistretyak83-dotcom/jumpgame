"""ViewFactory -- централизованная OCP-регистрация сущностей -> вью (Фаза 9).

Единственное место, где модель сопоставляется со своим CharacterView.
Game и Composition Root больше не строят лямбды-фабрики вручную --
они берут готовый реестр через ViewFactory. Это изолирует Presentation-слой
от оркестратора и убирает протечку знания типов (Player/Enemy) из Game/main.

Schema:
  build_default_registry(sprite_cache) -> {type: Callable[[], CharacterView]}
  register(cls, factory)               -> добавить новый тип без правки логики (OCP)
"""

from models.enemy import Enemy
from models.player import Player
from views.sprite_cache import SpriteCache


class ViewFactory:
    """Строит и хранит реестр «тип модели -> фабрика вью»."""

    def __init__(self, sprite_cache: SpriteCache):
        self._sprite_cache = sprite_cache
        self._registry: dict = {}

    def build_default_registry(self) -> dict:
        """Реестр по умолчанию: Player -> player_view, Enemy -> enemy_view.

        Поведение идентично бывшим лямбдам в Game/main.
        Возвращает копию (реестр при этом сохраняется внутри для register()).
        """
        cache = self._sprite_cache
        self._registry = {
            Player: cache.player_view,
            Enemy: lambda: cache.enemy_view(),
        }
        return dict(self._registry)

    def register(self, entity_cls, view_factory) -> None:
        """OCP: подключает вью для нового типа сущности без правки базовой логики."""
        self._registry[entity_cls] = view_factory

    @property
    def registry(self) -> dict:
        return dict(self._registry)