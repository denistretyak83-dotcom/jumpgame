"""PlayerFlow -- сервис смерти/респавна игрока и жизней (SRP, декомпозиция Game).

Выносит из Game ответственность за:
  - обработку смерти игрока (запуск анимации, проверка жизней),
  - потерю жизни через LifeManager,
  - респавн игрока на спавне уровня (создание нового экземпляра через
    WorldFactory.create_player и подмену ссылки),
  - сигнал Game о том, что жизни закончились (game over).

Game остаётся тонким оркестратором: вызывает PlayerFlow.update_death(dt)
в блоке смерти и, если вернётся "lives exhausted" (True), сам переключает
состояние в GAME_OVER. PlayerFlow никак не трогает state/рендер/камеру.
"""

from models.player import Player


class PlayerFlow:
    """Управляет жизнями и респавном игрока."""

    def __init__(self, world_factory, life_manager, event_bus):
        self._world_factory = world_factory
        self._life_manager = life_manager
        self._event_bus = event_bus
        self._level = None
        self.player: Player | None = None

    # ------------------------------------------------------------------
    # Привязка контекста (уровень и игрок), вызывается Game
    # ------------------------------------------------------------------
    def bind_level(self, level) -> None:
        """Связать текущий уровень (нужен спавн). Вызывается при загрузке."""
        self._level = level

    def bind_player(self, player: Player) -> None:
        """Привязать активного игрока (из LevelFlow)."""
        self.player = player

    # ------------------------------------------------------------------
    # Основной метод: обработка смерти за кадр
    # ------------------------------------------------------------------
    def update_death(self, dt) -> bool | None:
        """Обработать смерть игрока за кадр.

        Возвращает:
          - None, если игрок жив (не в состоянии смерти) или смерть ещё
            проигрывается;
          - True,  если жизни закончились -> Game должен объявить GAME_OVER;
          - False, если смерть завершилась и игрок респавнится (self.player
            уже заменён на нового).

        Не мутирует state/камеру/рендер — только жизни и своего игрока.
        """
        if self.player is None or not self.player.is_dead:
            return None
        if self.player.update_death(dt):
            # Анимация смерти завершилась -> обрабатываем жизни.
            if self._life_manager.lose_life():
                return True  # lives закончились -> game over
            self.respawn()  # есть жизни -> респавн
            return False
        return None  # смерть ещё проигрывается

    # ------------------------------------------------------------------
    def respawn(self) -> Player:
        """Создать нового игрока на спавне уровня и заменить self.player.

        Возвращает нового игрока, чтобы Game мог подменить ссылку в своём
        списке entities и перевести камеру.
        """
        spawn = self._level.player_spawn
        new_player = self._world_factory.create_player(spawn[0], spawn[1], self._event_bus)
        self.player = new_player
        return new_player

    # ------------------------------------------------------------------
    # Доступ к жизням (прокси, чтобы Game не лез внутрь LifeManager)
    # ------------------------------------------------------------------
    @property
    def lives(self) -> int:
        return self._life_manager.lives

    def reset_lives(self, count: int) -> None:
        self._life_manager.reset(count)
