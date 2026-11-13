"""RenderState -- data-class: все данные, необходимые Renderer за кадр.

Замена fat-interface Renderer.draw (~12 аргументов) на один объект (DIP/ISP).
Game._draw собирает RenderState и передаёт его в Renderer.draw(state).
Поля повторяют 1-в-1 прежние аргументы draw, чтобы рефакторинг был безопасным.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class RenderState:
    entities: list[Any]
    coins: list[Any]
    coin_collected: list[bool]
    flag_rect: Any
    score: int
    lives: int
    seconds: float  # счётчик кадров/время (HUD)
    state_manager: Any  # StateManager
    won: bool
    game_over: bool
    fade_level: float
    camera: Any  # ParallaxCamera (player_x для фона)
