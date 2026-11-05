"""WorldFactory -- Builds fresh model objects wired to shared assets/config.
  objects and passes them into this factory via the 'animations' argument.
- Entity construction is data-driven (takes dicts), not positional args.
"""
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
    def create_enemy(self, data, animations):
        # animations должен содержать 'walk' (или 'walk_left', 'walk_right')
        # Если анимаций нет, враг не будет виден
        if 'walk' not in animations:
            # Можно добавить дефолтную заглушку или ошибку
            pass

        return Enemy(
            x=data["x"],
            y=data["y"],
            left=data["left"],
            right=data["right"],
            animations=animations,
            config=self.config
        )

    def create_coin(self, entity_data: dict):
        """Simple data-driven factory for collectibles."""
        # If you have a Coin model, instantiate it here.
        # Otherwise, just return the rect data for the view to handle.
        return entity_data.get("rect")

    def create_platform(self, entity_data: dict):
        """Factory for platform geometry."""
        return entity_data.get("rect")

    # ------------------------------------------------------------------
    # Special Instance Methods (used by Game/Controllers)
    # ------------------------------------------------------------------

    def create_player(self, x, y, animations, sounds=None):
        """
        Build a Player with the given spawn coordinates.
        """
        # Передаем весь объект settings в Player, чтобы он знал свои настройки
        return Player(x, y, animations, sounds, settings)

    # ------------------------------------------------------------------
    # Asset Helpers (Internal / View Layer Support)
    # ------------------------------------------------------------------

    def load_player_frames(self):
        """Returns raw frame lists. Views/Controllers wrap these into Animation objects."""
        size = (self.config.player.width, self.config.player.height)
        return {
            'idle': self.assets.load_animation_frames("player_idle", 3, size),
            'run_l': self.assets.load_animation_frames("player_run/left", 4, size),
            'run_r': self.assets.load_animation_frames("player_run/right", 4, size),
            'jump': self.assets.load_animation_frames("player_jump", 2, size),
        }

    def load_enemy_frames(self):
        """Returns raw walk frame list."""
        size = (self.config.enemy.width, self.config.enemy.height)
        return {
            'walk': self.assets.load_animation_frames("enemy_walk", 4, size),
        }