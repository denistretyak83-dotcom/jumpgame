"""LevelTransition -- сервис каталога уровней и переходов (SRP, декомпозиция Game).

Выносит из Game ответственность за:
  - текущий загруженный уровень (current_level_name),
  - загрузку уровня по имени (обёртка над LevelFlow),
  - переход на следующий уровень через next_level (каталог уровней),
  - рестарт игры (возврат на первый уровень каталога).

Game остаётся тонким оркестратором: держит ссылку на LevelTransition и
после каждого вызова забирает из него актуальные поля (level, player,
entities, coins, coin_collected) для точек входа рендера/коллизий.
LevelTransition не трогает state/рендер/камеру — только загрузку миров.
"""

from core.level_flow import LevelFlow


class LevelTransition:
    """Управляет загрузкой уровней и переходами по каталогу."""

    def __init__(self, level_manager, level_flow: LevelFlow):
        self._level_manager = level_manager
        self._level_flow = level_flow
        self.current_level_name: str | None = None

    # ------------------------------------------------------------------
    # Загрузка конкретного уровня
    # ------------------------------------------------------------------
    def load_level(self, level_name: str) -> dict:
        """Загрузить уровень по имени и вернуть построенный мир.

        Возвращает dict с полями level/player/entities/coins/coin_collected,
        которые Game заберёт и разложит по своим атрибутам. Обновляет
        current_level_name.
        """
        self._level_flow.load_and_setup(level_name)
        self.current_level_name = level_name
        return {
            "level": self._level_flow.level,
            "player": self._level_flow.player,
            "entities": self._level_flow.entities,
            "coins": self._level_flow.coins,
            "coin_collected": self._level_flow.coin_collected,
        }

    # ------------------------------------------------------------------
    # Переход на следующий уровень по next_level
    # ------------------------------------------------------------------
    def advance_to_next_level(self) -> dict | None:
        """Перейти на следующий уровень по цепочке next_level.

        Возвращает построенный мир следующего уровня (как load_level), или
        None, если следующего уровня нет (текущий — последний в каталоге).
        """
        next_name = self._level_manager.next_level_name(self.current_level_name)
        if next_name is None:
            return None
        return self.load_level(next_name)

    def has_next_level(self) -> bool:
        """True, если у текущего уровня есть следующий (next_level != None)."""
        return self._level_manager.next_level_name(self.current_level_name) is not None

    # ------------------------------------------------------------------
    # Рестарт: возврат на первый уровень каталога
    # ------------------------------------------------------------------
    def restart_first(self) -> dict:
        """Рестарт игры: загрузить первый уровень каталога ("level_1").

        Возвращает построенный мир, как load_level.
        """
        return self.load_level("level_1")
