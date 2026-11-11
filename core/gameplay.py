"""CollisionDirector -- обработка коллизий в игровые правила (Gameplay).

Вынесено из Game (SRP / декомпозиция God-Object, Фаза 3).
Принимает результат CollisionSystem.check() и применяет игровые правила:
монета (счёт/событие/звук), враг (смерть), флаг (победа), падение (смерть).

Правила держит ЗДЕСЬ, а не в Game. Сам не знает про Renderer/Input.
Зависимости инжектируются через конструктор (DI).
"""

from core.event_bus import GameEvents
from core.state_manager import GameState


class CollisionDirector:
    """Применяет результат проверки коллизий к игровому состоянию."""

    def __init__(self, collision_system, score_manager, event_bus, sounds, state):
        self.collision_system = collision_system
        self.score_manager = score_manager
        self.event_bus = event_bus
        self.sounds = sounds
        self.state = state
        self.won = False  # флаг победы, читается Game'ом для _draw и т.п.

    def process(self, player, coins, coin_collected, entities, flag_rect) -> None:
        """Один проход коллизий за кадр → применяет игровые правила."""
        c = self.collision_system.check(
            player.rect,
            coins,
            coin_collected,
            [e for e in entities if e is not player],
            flag_rect,
        )

        # --- монета ---
        if c.coin_index is not None:
            coin_collected[c.coin_index] = True
            self.score_manager.add_points(1)
            self.event_bus.emit(GameEvents.COIN_COLLECTED, self.score_manager.score)
            self.sounds.play_coin()

        # --- враг ---
        if c.hit_enemy is not None:
            self.event_bus.emit(GameEvents.PLAYER_DIED)
            player.die(launch_up=False)

        # --- флаг ---
        if c.hit_flag:
            self.event_bus.emit(GameEvents.LEVEL_WON)
            self.won = True
            self.state.set(GameState.WON)
            self.sounds.play_win()

        # --- падение ---
        if c.fell_out:
            self.event_bus.emit(GameEvents.PLAYER_DIED)
            player.die(launch_up=False)
