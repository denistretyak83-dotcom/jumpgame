"""CollisionSystem -- централизует все проверки коллизий в один проход (R6).

Проверяет ВСЕ коллизии за один вызов и возвращает структурированный
CollisionResult БЕЗ мутаций игры. Игровые правила остаются в Game.

Исправления по аудиту:
- Интерфейс Collidable (Protocol) вместо сырого duck-typing (ISP/DIP).
- fall_buffer берётся из settings.json, а не захардкожен.
"""

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from core.geometry import RectPosition


@runtime_checkable
class Collidable(Protocol):
    """Что нужно сущности, чтобы участвовать в коллизиях."""

    rect: RectPosition


@dataclass
class CollisionResult:
    """Результат одного прохода коллизий за кадр (data-driven, без мутаций)."""

    coin_index: int | None = None  # индекс подобранной монеты (или None)
    hit_enemy: Any | None = None  # враг, с которым столкнулись (или None)
    hit_flag: bool = False  # коснулись флага
    fell_out: bool = False  # упали ниже экрана


class CollisionSystem:
    """Проверяет ВСЕ коллизии за один проход.

    Чистая функция: принимает состояние, возвращает CollisionResult.
    Сам НЕ эмитит события и не меняет score/lives — это делает Game.
    """

    def __init__(self, screen_height: int, fall_buffer: int):
        self.screen_height = screen_height
        self.fall_buffer = fall_buffer  # теперь из settings, не магия

    def check(
        self,
        player_rect: RectPosition,
        coins: list[RectPosition],
        coin_collected: list[bool],
        enemies: list[Collidable],
        flag_rect: RectPosition | None,
    ) -> CollisionResult:
        """Один проход: монеты -> враг -> флаг -> падение."""
        result = CollisionResult()

        # 1. Монеты — первая попавшаяся неподобранная
        for i, coin in enumerate(coins):
            if not coin_collected[i] and player_rect.intersects(coin):
                result.coin_index = i
                break

        # 2. Враг — первое пересечение (у врагов есть .rect -> Collidable)
        for enemy in enemies:
            if player_rect.intersects(enemy.rect):
                result.hit_enemy = enemy
                break

        # 3. Флаг
        if flag_rect is not None and player_rect.intersects(flag_rect):
            result.hit_flag = True

        # 4. Падение за нижний край экрана (+буфер)
        if player_rect.bottom > self.screen_height + self.fall_buffer:
            result.fell_out = True

        return result
