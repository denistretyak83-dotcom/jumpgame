"""audio_listener.py -- переводит события модели в звуки.

Подписывается на player.* события EventBus и вызывает SoundManager.
Развязывает Player и SoundManager (SRP + Observer).

Вызывается из Game.__init__ через attach_audio_listener(event_bus, sounds).
"""
from core.event_bus import GameEvents


def attach_audio_listener(event_bus, sounds):
    """Подписывает звуки на события игрока.

    Args:
        event_bus: EventBus (core/event_bus.py).
        sounds: SoundManager (audio/sound_manager.py) или None.
    """
    if not sounds:
        return

    event_bus.subscribe(GameEvents.PLAYER_JUMP, sounds.play_jump)
    event_bus.subscribe(GameEvents.PLAYER_DIED, sounds.play_death)
    event_bus.subscribe(GameEvents.PLAYER_BUMP, sounds.play_bump)
