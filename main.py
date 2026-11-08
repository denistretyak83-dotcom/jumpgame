"""Jump & Reach the Flag -- MVC entry point (thin)."""
import pathlib
import pygame
from core.config import settings
from core.logger import GameLogger
from core.game import Game


def main():
    pygame.init()
    logger = GameLogger(config=settings.logging)
    game = Game(logger=logger)
    game.run()
    return 0


if __name__ == "__main__":
    main()
