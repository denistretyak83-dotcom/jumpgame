"""Фаза 12: контракт PlayableCharacter (DIP/ISP) + любые герои через Protocol."""

import pytest

from models.playable_character import PlayableCharacter


class _FakeDeathCfg:
    gravity = 1200
    launch_vy = -400
    fall_vy = -100
    margin = 60


class _FakePhysicsCfg:
    gravity = 1500
    jump_strength = -650
    max_fall = 1400


class _FakePlayerCfg:
    width = 40
    height = 50
    speed = 350


class _FakeScreen:
    height = 600


class _FakeAnim:
    idle_delay = 0.167
    run_delay = 0.10
    jump_delay = 0.13
    walk_delay = 0.13


class _FakeConfig:
    death = _FakeDeathCfg()
    physics = _FakePhysicsCfg()
    player = _FakePlayerCfg()
    screen = _FakeScreen()
    animation = _FakeAnim()


def _make_player():
    from models.player import Player

    return Player(10, 100, config=_FakeConfig())


def test_player_satisfies_playable_character_protocol():
    from models.player import Player

    assert isinstance(Player, PlayableCharacter) is False  # это класс, не экземпляр
    player = _make_player()
    assert isinstance(player, PlayableCharacter) is True


def test_playable_character_has_required_attributes():
    player = _make_player()
    for attr in ("rect", "vel_x", "vel_y", "on_ground", "is_dead"):
        assert hasattr(player, attr), f"не хватает атрибута {attr}"
    for method in ("update", "apply_physics", "get_visual_data", "die", "spawn_copy"):
        assert callable(getattr(player, method)), f"не хватает метода {method}"


def test_playable_character_runtime_check_with_plain_obj():
    # обычный объект без контракта — не считается играемым персонажем
    class NotAPlayer:
        pass

    assert isinstance(NotAPlayer(), PlayableCharacter) is False