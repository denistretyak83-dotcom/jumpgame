"""Точка входа приложения.

DI-связка (R3): единственное место создания Settings() и GameLogger().
Никаких глобальных импортов настроек/логгера — все зависимости инжектируются
через конструкторы.
"""

import pygame

from core.config import Settings  # класс, а не глобальный экземпляр
from core.game import Game
from core.logger import GameLogger


def main():
    pygame.init()

    # 1) Создаём конфигурацию приложения (читает settings.json)
    settings = Settings()

    # 2) Логгер — с настройками ротации из конфига
    logger = GameLogger(config=settings.logging)

    # 3) Инжектируем И config, И logger в игру
    game = Game(config=settings, logger=logger)
    game.run()
    return 0


if __name__ == "__main__":
    main()
