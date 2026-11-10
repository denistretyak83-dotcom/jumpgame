"""Тесты StateManager: игровые состояния, переходы, флаги."""
import pytest

from core.state_manager import StateManager, GameState


def test_initial_state_defaults_to_playing():
    sm = StateManager()
    assert sm.state is GameState.PLAYING
    assert sm.previous is None


def test_initial_state_custom():
    sm = StateManager(initial=GameState.WON)
    assert sm.current is GameState.WON


def test_set_records_previous():
    sm = StateManager()
    assert sm.previous is None
    sm.set(GameState.GAME_OVER)
    assert sm.state is GameState.GAME_OVER
    assert sm.previous is GameState.PLAYING


def test_set_multiple_transitions_track_previous():
    sm = StateManager(GameState.PLAYING)
    sm.set(GameState.WON)
    sm.set(GameState.PLAYING)   # перезапуск
    assert sm.state is GameState.PLAYING
    assert sm.previous is GameState.WON


def test_is_playing_true_when_playing():
    sm = StateManager(GameState.PLAYING)
    assert sm.is_playing() is True


def test_is_playing_false_after_end():
    sm = StateManager(GameState.WON)
    assert sm.is_playing() is False


def test_has_ended_for_won_and_game_over():
    assert StateManager(GameState.WON).has_ended() is True
    assert StateManager(GameState.GAME_OVER).has_ended() is True
    assert StateManager(GameState.PLAYING).has_ended() is False


def test_current_property_returns_state():
    sm = StateManager(GameState.GAME_OVER)
    assert sm.current is GameState.GAME_OVER
    sm.set(GameState.PLAYING)
    assert sm.current is GameState.PLAYING