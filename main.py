"""Jump & Reach the Flag -- MVC entry point (thin)."""
import pathlib
import pygame
from core.game import Game


def main():
    pygame.init()
    root_dir = str(pathlib.Path(__file__).resolve().parent)
    game = Game(root_dir=root_dir)
    game.run()
    return 0


if __name__ == "__main__":
    main()
