"""StateManager -- central game state (playing / won / game over)."""

from enum import Enum, auto


class GameState(Enum):
    PLAYING = auto()  # normal gameplay
    WON = auto()  # flag reached -> show victory + allow restart
    GAME_OVER = auto()  # lives exhausted -> pixelated fade


class StateManager:
    """Tracks the current game state and the previous state."""

    def __init__(self, initial: GameState = GameState.PLAYING):
        self.state = initial
        self.previous = None

    def set(self, new_state: GameState):
        self.previous = self.state
        self.state = new_state

    @property
    def current(self):
        return self.state

    def is_playing(self):
        return self.state is GameState.PLAYING

    def has_ended(self):
        return self.state in (GameState.WON, GameState.GAME_OVER)
