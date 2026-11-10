"""Паттерн Состояние (State pattern / FSM) для игрока.

Каждое состояние знает:
- anim_key — какую анимацию показывать;
- handle() — условия перехода в другое состояние.

Добавление новых возможностей (удар, ползанье, двойной прыжок) =
новый класс-состояние + регистрация переходов. Существующие НЕ меняются (OCP).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional



class PlayerState(ABC):
    """Базовое состояние игрока."""

    # ------------- анимация -------------
    @property
    @abstractmethod
    def anim_key(self) -> str:
        """Ключ анимации (idle/run/jump/...)."""

    def get_anim_key(self, player) -> str:
        """По умолчанию возвращает свою анимацию. При необходимости переопределяется."""
        return self.anim_key

    # ------------- хуки жизни состояния -------------
    def enter(self, player) -> None:
        """Вызывается при входе (например, задать vel_y при прыжке)."""

    def exit(self, player) -> None:
        """Вызывается при выходе из состояния."""

    # ------------- переходы -------------
    @abstractmethod
    def handle(self, player, intent, dt) -> Optional["PlayerState"]:
        """Возвращает новое состояние или None, если остаёмся в текущем."""


# ---------------------------------------------------------------------------
# Состояния покоя / движения
# ---------------------------------------------------------------------------

class IdleState(PlayerState):
    anim_key = 'idle'

    def handle(self, player, intent, dt):
        if not player.on_ground:
            return JumpState() if player.vel_y < 0 else FallState()
        if intent and intent.jump_pressed:
            return JumpState()
        if player.vel_x != 0:
            return RunState()
        return None


class RunState(PlayerState):
    anim_key = 'run'

    def handle(self, player, intent, dt):
        if not player.on_ground:
            return JumpState() if player.vel_y < 0 else FallState()
        if intent and intent.jump_pressed:
            return JumpState()
        if player.vel_x == 0:
            return IdleState()
        return None


# ---------------------------------------------------------------------------
# Состояния полёта (прыжок вверх / падение вниз)
# ---------------------------------------------------------------------------

class JumpState(PlayerState):
    """Летим ВВЕРХ (vel_y < 0). Это настоящий прыжок."""

    anim_key = 'jump'     # ← реализует абстрактное свойство (не абстрактно больше)

    def enter(self, player):
        self._moving = player.vel_x != 0

    def get_anim_key(self, player) -> str:
        # реальный выбор: направленный или нейтральный
        return 'jump' if player.vel_x != 0 else 'jump_neutral'

    def handle(self, player, intent, dt):
        self._moving = player.vel_x != 0
        if player.vel_y >= 0:
            return FallState()
        return None


class FallState(PlayerState):
    """Падаем ВНИЗ (vel_y >= 0) — сход с платформы, не прыжок."""

    anim_key = 'idle'     # значение по умолчанию (удовлетворяет ABC)

    def enter(self, player):
        self._moving = player.vel_x != 0

    def get_anim_key(self, player) -> str:
        return 'run' if player.vel_x != 0 else 'idle'

    def handle(self, player, intent, dt):
        if player.on_ground:
            return IdleState() if player.vel_x == 0 else RunState()
        if player.vel_y < 0:
            return JumpState()
        return None


# ---------------------------------------------------------------------------
# Машина состояний
# ---------------------------------------------------------------------------

class PlayerStateMachine:
    """Владелец текущего состояния игрока."""

    def __init__(self, initial_state: Optional[PlayerState] = None):
        self._state: PlayerState = initial_state or IdleState()

    @property
    def state(self) -> PlayerState:
        return self._state

    def handle(self, player, intent, dt) -> PlayerState:
        """Обновляет состояние: вызывает handle текущего, при переходе — хуки."""
        new_state = self._state.handle(player, intent, dt)
        if new_state is not None and not isinstance(new_state, type(self._state)):
            self._state.exit(player)
            self._state = new_state
            self._state.enter(player)
        return self._state

    def get_anim_key(self, player) -> str:
        """Актуальный ключ анимации от текущего состояния."""
        return self._state.get_anim_key(player)