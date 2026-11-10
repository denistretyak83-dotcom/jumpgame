"""Тесты машины состояний игрока (models/player_state.py, без pygame)."""

from models.player_state import IdleState, JumpState, FallState, RunState, PlayerStateMachine


class _Intent:
    def __init__(self):
        self.jump_pressed = False


class _FakePlayer:
    """Минимальный объект-заглушка с полями, которые читает state machine."""

    def __init__(self, on_ground=True, vel_x=0.0, vel_y=0.0):
        self.on_ground = on_ground
        self.vel_x = vel_x
        self.vel_y = vel_y


def _pm():
    return PlayerStateMachine(IdleState())


def test_default_state_is_idle():
    assert isinstance(_pm().state, IdleState)


def test_stand_still_stays_idle():
    pm = _pm()
    player = _FakePlayer(on_ground=True, vel_x=0)
    pm.handle(player, _Intent(), 0.016)
    assert isinstance(pm.state, IdleState)


def test_moving_transitions_to_run():
    pm = _pm()
    player = _FakePlayer(on_ground=True, vel_x=120)
    pm.handle(player, _Intent(), 0.016)
    assert isinstance(pm.state, RunState)


def test_jump_pressed_transitions_to_jump():
    pm = _pm()
    player = _FakePlayer(on_ground=True, vel_x=0)
    intent = _Intent()
    intent.jump_pressed = True
    pm.handle(player, intent, 0.016)
    assert isinstance(pm.state, JumpState)


def test_high_position_fall_back_to_ground():
    # Из воздушного состояния (vel_y<0 — вверх) после прохождения вершины
    pm = PlayerStateMachine(JumpState())
    player = _FakePlayer(on_ground=False, vel_x=0, vel_y=120)  # уже падает вниз
    pm.handle(player, _Intent(), 0.016)
    assert isinstance(pm.state, FallState)
