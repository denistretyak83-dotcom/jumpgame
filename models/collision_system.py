"""CollisionSystem -- centralizes all collision checks into a single pass (R6).

Ср. со старым models/collision.py (чистые функции-проверки):
теперь все проверки собраны в ОДНУ систему, которая за один вызов возвращает
структурированный результат и НЕ мутирует игру/score/lives. Игровые правила
остаются в Game (оркестраторе).
"""
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class CollisionResult:
    """Результат одного прохода коллизий за кадр (data-driven, без мутаций)."""
    coin_index: Optional[int] = None     # индекс подобранной монеты (или None)
    hit_enemy: Optional[Any] = None      # враг, с которым столкнулись (или None)
    hit_flag: bool = False               # коснулись флага
    fell_out: bool = False               # упали ниже экрана


class CollisionSystem:
    """Проверяет ВСЕ коллизии за один проход.

    Чистая функция: принимает состояние, возвращает CollisionResult.
    Сам НЕ эмитит события и не меняет score/lives — это делает Game.
    """

    def __init__(self, screen_height: int, fall_buffer: int = 30):
        self.screen_height = screen_height
        self.fall_buffer = fall_buffer

    def check(self, player_rect, coins: List, coin_collected: List[bool],
              enemies: List, flag_rect) -> CollisionResult:
        """Один проход: монеты -> враг -> флаг -> падение."""
        result = CollisionResult()

        # 1. Монеты — первая попавшаяся неподобранная
        for i, coin in enumerate(coins):
            if not coin_collected[i] and player_rect.colliderect(coin):
                result.coin_index = i
                break

        # 2. Враг — первый пересечение (у врагов есть .rect)
        for enemy in enemies:
            if player_rect.colliderect(enemy.rect):
                result.hit_enemy = enemy
                break

        # 3. Флаг
        if flag_rect is not None and player_rect.colliderect(flag_rect):
            result.hit_flag = True

        # 4. Падение за нижний край экрана (+буфер)
        if player_rect.bottom > self.screen_height + self.fall_buffer:
            result.fell_out = True

        return result