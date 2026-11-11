"""AssetLoader -- loads fonts and sprite frames with caching.

DI (R3): конфиг инжектируется через конструктор; если не передан,
создаётся собственный Settings() (но не читается глобальный).
"""

import os

import pygame

from core.config import Settings


class AssetLoader:
    """Caches fonts and sprite surfaces so they are only loaded once."""

    def __init__(self, base_dir, config=None):
        self.base_dir = base_dir
        self.config = config or Settings()
        self.font_cache = {}
        self.surface_cache = {}
        self._setup_roots()

    def _setup_roots(self):
        self.fonts_abs = os.path.join(self.base_dir, self.config.assets.fonts_dir)
        self.sprites_abs = os.path.join(self.base_dir, self.config.assets.sprites_dir)
        self.sounds_abs = os.path.join(self.base_dir, self.config.assets.sounds_dir)

    def get_font(self, size, name=None):
        name = name or self.config.assets.font_name
        key = (name, size)
        if key not in self.font_cache:
            path = os.path.join(self.fonts_abs, name)
            try:
                self.font_cache[key] = pygame.font.Font(path, size)
            except FileNotFoundError:
                self.font_cache[key] = pygame.font.Font(None, size)
        return self.font_cache[key]

    def load_image(self, relative, scale=None):
        key = (relative, scale)
        if key not in self.surface_cache:
            path = os.path.join(self.sprites_abs, relative)
            img = pygame.image.load(path).convert_alpha()
            if scale is not None:
                img = pygame.transform.scale(img, scale)
            self.surface_cache[key] = img
        return self.surface_cache[key]

    def load_animation_frames(self, folder, frame_count, scale):
        frames = []
        for i in range(1, frame_count + 1):
            rel = os.path.join(folder, f"{i}.png")
            frames.append(self.load_image(rel, scale))
        return frames
