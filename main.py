"""Точка входа приложения — Composition Root (DIP, шаг 4).

Единственное место создания ВСЕХ внешних зависимостей инфраструктуры:
Settings, GameLogger, pygame-окно, рендер, ресурсы, звук, фабрика мира.
Game получает их через services (DIP) и больше ничего не создаёт сам.
"""

import pathlib

import pygame

from audio.sound_manager import SoundManager
from core.asset_loader import AssetLoader
from core.config import Settings  # класс, а не глобальный экземпляр
from core.game import Game
from core.logger import GameLogger
from models.factory import WorldFactory
from views.renderer import Renderer
from views.sprite_cache import SpriteCache


def _make_coin_icon(screen_conf, assets_conf):
    """Небольшой помощник: пиксельная иконка монеты (вынесена из Game)."""
    icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(icon, (255, 200, 0), (8, 8), 7)
    pygame.draw.circle(icon, (255, 240, 100), (6, 6), 4)
    return icon


def build_services(settings, logger, root_dir):
    """Собрать все внешние зависимости игры (Composition Root)."""
    root = pathlib.Path(root_dir)

    # --- Ресурсы и звук (группа связанности) ---
    asset_loader = AssetLoader(str(root), settings)
    sounds = SoundManager(asset_loader.sounds_abs)

    # --- Окно ---
    screen = pygame.display.set_mode((settings.screen.width, settings.screen.height))
    pygame.display.set_caption(settings.screen.caption)

    # --- View-слой (группа: screen/sprite_cache/coin_icon/renderer) ---
    sprite_cache = SpriteCache(asset_loader, settings)
    font = asset_loader.get_font(settings.assets.font_size)
    small_font = asset_loader.get_font(settings.assets.small_font_size)
    coin_icon = _make_coin_icon(settings.screen, settings.assets)
    renderer = Renderer(
        screen,
        sprite_cache,
        coin_icon,
        font,
        small_font,
        settings,
        view_registry={
            __import__("models.player", fromlist=["Player"]).Player: lambda: (
                sprite_cache.player_view()
            ),
            __import__("models.enemy", fromlist=["Enemy"]).Enemy: lambda: sprite_cache.enemy_view(),
        },
    )

    # --- Фабрика мира ---
    world_factory = WorldFactory(asset_loader, settings)

    return {
        "asset_loader": asset_loader,
        "sounds": sounds,
        "screen": screen,
        "sprite_cache": sprite_cache,
        "coin_icon": coin_icon,
        "renderer": renderer,
        "world_factory": world_factory,
    }


def main():
    pygame.init()

    # 1) Конфигурация приложения (читает settings.json)
    settings = Settings()

    # 2) Логгер — с настройками ротации из конфига
    logger = GameLogger(config=settings.logging)

    # 3) Composition Root: собрать внешние зависимости
    root_dir = str(pathlib.Path(__file__).resolve().parent)
    services = build_services(settings, logger, root_dir)

    # 4) Игра получает всё через services (DIP); config/logger тоже инжектируются
    game = Game(config=settings, logger=logger, root_dir=root_dir, services=services)

    game.run()
    return 0


if __name__ == "__main__":
    main()
