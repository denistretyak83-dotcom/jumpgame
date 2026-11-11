"""LevelFlow -- жизненный цикл уровня: загрузка и построение мира (декомпозиция Game).

Вынесено из Game.reset_run_state (SRP, Фаза 3). Отвечает за:
- загрузку уровня через LevelManager;
- построение мира: игрок, враги (spawn_copy), монеты, платформы;
- рестарт уровня (сброс).

Не знает про рендер деталей/ввод. Зависимости инжектируются (DI).
"""


class LevelFlow:
    """Оркестрирует загрузку уровня и сборку списка сущностей мира."""

    def __init__(self, level_manager, world_factory, event_bus, renderer, camera, sounds):
        self.level_manager = level_manager
        self.world_factory = world_factory
        self.event_bus = event_bus
        self.renderer = renderer
        self.camera = camera
        self.sounds = sounds

        # Состояние мира (заполняется при загрузке уровня)
        self.level = None
        self.player = None
        self.entities = []
        self.coins = []
        self.coin_collected = []

    def load_and_setup(self, level_name: str = "level_1"):
        """Загружает уровень, строит мир, обновляет камеру/музыку.

        Возвращает LevelData. Заполняет: level, player, entities, coins,
        coin_collected.
        """
        level_data = self.level_manager.load_level(level_name)
        self.level = level_data
        self.renderer.set_platforms(level_data.platforms)

        spawn = level_data.player_spawn
        self.player = self.world_factory.create_player(spawn[0], spawn[1], self.event_bus)
        self.entities = [self.player] + [e.spawn_copy() for e in level_data.enemies]
        self.coins = [r.copy() for r in level_data.coins]
        self.coin_collected = [False] * len(self.coins)

        self.camera.update(self.player.rect.x)
        self.sounds.play_music()
        return level_data
