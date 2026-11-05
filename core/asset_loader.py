"""AssetLoader -- loads fonts and sprite frames with caching."""
import os
import pygame
from core.config import settings


class AssetLoader:
    """Caches fonts and sprite surfaces so they are only loaded once."""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.font_cache = {}
        self.surface_cache = {}
        self._setup_roots()

    def _setup_roots(self):
        self.fonts_abs = os.path.join(self.base_dir, settings.assets.fonts_dir)
        self.sprites_abs = os.path.join(self.base_dir, settings.assets.sprites_dir)
        self.sounds_abs = os.path.join(self.base_dir, settings.assets.sounds_dir)

    # ---- fonts ----
    def get_font(self, size, name=None):
        name = name or settings.assets.font_name
        key = (name, size)
        if key not in self.font_cache:
            path = os.path.join(self.fonts_abs, name)
            try:
                self.font_cache[key] = pygame.font.Font(path, size)
            except FileNotFoundError:
                # Fall back to a default font if the pixel font is missing
                self.font_cache[key] = pygame.font.Font(None, size)
        return self.font_cache[key]

    # ---- sprites ----
    def load_image(self, relative, scale=None):
        """Load an image by relative path under sprites/ and cache it."""
        key = (relative, scale)
        if key not in self.surface_cache:
            path = os.path.join(self.sprites_abs, relative)
            img = pygame.image.load(path).convert_alpha()
            if scale is not None:
                img = pygame.transform.scale(img, scale)
            self.surface_cache[key] = img
        return self.surface_cache[key]

    def load_animation_frames(self, folder, frame_count, scale):
        """Load frames 1..frame_count from sprites/<folder>/ as a list."""
        frames = []
        for i in range(1, frame_count + 1):
            rel = os.path.join(folder, f"{i}.png")
            frames.append(self.load_image(rel, scale))
        return frames
