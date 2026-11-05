"""Camera -- parallax scrolling for background layers."""
from core.config import settings


class ParallaxCamera:
    """Computes parallax layer offsets from the player x position."""

    def __init__(self):
        self.player_x = 0.0
        # ⚠️ ИЗМЕНЕНИЕ: Доступ теперь через объект screen
        self.width = settings.screen.width
        self.height = settings.screen.height

    def update(self, player_x):
        """Record the current world player x used for parallax."""
        self.player_x = float(player_x)

    def layer_offset(self, factor, repeat_width=None):
        """Return the wrapped x offset for a layer scrolling at `factor`."""
        if repeat_width is None:
            repeat_width = self.width
        return -(self.player_x * factor) % repeat_width

    def apply(self, x, factor, repeat_width=None):
        """Convenience: offset a fixed x by a parallax layer offset."""
        return x + self.layer_offset(factor, repeat_width)