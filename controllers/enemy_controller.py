"""EnemyController -- patrol AI for all enemies."""

from core.config import settings


class EnemyController:
    def __init__(self, config=None):
        self.config = config or settings

    def update_all(self, enemies, dt):
        """Update every enemy's patrol movement using Delta Time."""
        for e in enemies:
            e.update(dt)  # <-- Передаем dt во врага
