"""PlayerController -- тонкий слой транслирования ввода."""
import pygame


class PlayerController:
    def __init__(self):
        pass

    def get_keys(self):
        return pygame.key.get_pressed()

    def handle_input(self, player, keys, dt):
        """
        Этот метод вызывается из game.py, чтобы не было ошибки.
        Реальная логика движения находится в player.update(keys, ...).
        """
        pass