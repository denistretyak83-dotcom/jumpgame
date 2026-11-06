from models.player import Player
from models.enemy import Enemy
from core.config import settings


class WorldFactory:
    def __init__(self, asset_loader, config=None):
        self.assets = asset_loader
        self.config = config or settings

    # ------------------------------------------------------------------
    # Data-Driven Methods (used by LevelBuilder)
    # ------------------------------------------------------------------

    def create_enemy(self, data):
        """Строит врага из данных уровня (без animations -- теперь View)."""
        return Enemy(
            x=data["x"],
            y=data["y"],
            left=data["left"],
            right=data["right"],
            config=self.config
        )

    def create_coin(self, entity_data: dict):
        return entity_data.get("rect")

    def create_platform(self, entity_data: dict):
        return entity_data.get("rect")

    # ------------------------------------------------------------------
    # Special Instance Methods (used by Game/Controllers)
    # ------------------------------------------------------------------

    def create_player(self, x, y, event_bus=None):
        """Build Player with spawn coords. event_bus для эмита событий."""
        return Player(x, y, config=self.config, event_bus=event_bus)

    # ------------------------------------------------------------------
    # Asset Helpers больше НЕ нужны для построения юнитов --
    # анимации загружает SpriteCache (View-слой). Эти методы можно удалить.
    # ------------------------------------------------------------------