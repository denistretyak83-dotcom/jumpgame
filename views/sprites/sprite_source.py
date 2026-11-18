"""
views/sprites/sprite_source.py — контракт источника кадров (ФР-1).

SpriteCache получает кадры ЕДИНООБРАЗНО: и из PNG-ассетов (AssetLoader),
и из procedural-генератора (ФР-2). Это ключ к расширяемости графики (OCP):
новый источник регистрируется в SpriteCache, не трогая логику рендера.

View (CharacterView) по-прежнему получает готовые Animation; кадры строятся
из источника в SpriteCache.
"""

from typing import Protocol, runtime_checkable

import pygame


@runtime_checkable
class SpriteSource(Protocol):
    """Что умеет источник кадров (PNG или procedural)."""

    def frames(self, key: str, frame_count: int) -> list[pygame.Surface]:
        """Кадры анимации по ключу (player_idle/run/.../enemy_walk)."""

    def size(self) -> tuple[int, int]:
        """Размер спрайта (ширина, высота)."""

    def supports(self, key: str) -> bool:
        """Умеет ли источник отдать кадры для key."""


class PngSpriteSource:
    """Обёртка над AssetLoader: читает кадры из PNG-ассетов.

    Реализует SpriteSource. `size()` — размер спрайта (по умолчанию
    берётся размер игрока; для врагов используется в момент запроса).
    """

    _SUPPORTED_PLAYER = ("player_idle", "player_run/left", "player_run/right", "player_jump")
    _SUPPORTED_ENEMY = ("enemy_walk",)

    def __init__(self, asset_loader, config):
        self._assets = asset_loader
        self._cfg = config
        self._size = (
            self._cfg.player.width,
            self._cfg.player.height,
        )

    def size(self) -> tuple[int, int]:
        return self._size

    def supports(self, key: str) -> bool:
        return key in self._SUPPORTED_PLAYER or key in self._SUPPORTED_ENEMY

    def frames(self, key: str, frame_count: int) -> list[pygame.Surface]:
        """Загружает кадры из AssetLoader.

        Для врагов размер берётся из config.enemy, для игрока — из config.player.
        """
        if key in self._SUPPORTED_ENEMY:
            scale = (self._cfg.enemy.width, self._cfg.enemy.height)
        else:
            scale = self._size
        return self._assets.load_animation_frames(key, frame_count, scale)
