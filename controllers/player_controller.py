from dataclasses import dataclass

import pygame


@dataclass
class PlayerIntent:
    """Нейтральное представление действий игрока (без привязки к клавишам)."""

    left: bool = False
    right: bool = False
    jump: bool = False
    jump_pressed: bool = False  # True только в момент нажатия (edge detection)


class PlayerController:
    """ЕДИНСТВЕННОЕ место, читающее клавиатуру.

    Преобразует pygame keys -> PlayerIntent.
    Ничего не знает о физике/анимации/звуках.
    """

    def __init__(self, jump_keys=None, left_keys=None, right_keys=None):
        self._jump_keys = jump_keys or (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
        self._left_keys = left_keys or (pygame.K_LEFT, pygame.K_a)
        self._right_keys = right_keys or (pygame.K_RIGHT, pygame.K_d)
        self._prev_jump = False  # для edge detection прыжка

    def get_keys(self):
        return pygame.key.get_pressed()

    def handle_input(self, keys=None) -> PlayerIntent:
        """Собирает состояние клавиш в PlayerIntent.

        Если keys не передан -- читает live.
        Прыжок: jump=True пока зажата, jump_pressed=True только в момент нажатия.
        """
        if keys is None:
            keys = self.get_keys()

        jump_held = any(keys[k] for k in self._jump_keys)
        intent = PlayerIntent(
            left=any(keys[k] for k in self._left_keys),
            right=any(keys[k] for k in self._right_keys),
            jump=jump_held,
            jump_pressed=(jump_held and not self._prev_jump),
        )
        self._prev_jump = jump_held
        return intent
