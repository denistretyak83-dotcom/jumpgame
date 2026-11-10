"""Тесты BaseCharacter: абстракции, смерть, возрождение, физика."""
import importlib.util

import pytest

pygame_available = importlib.util.find_spec("pygame") is not None

from models.base_character import BaseCharacter  # noqa: E402
from models.physics import PhysicsComponent  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pygame_available, reason="pygame недоступен (нужен pygame.Rect)"
)


# Конкретный подкласс (BaseCharacter абстрактный)
class DummyCharacter(BaseCharacter):
    def update(self, dt, ctx=None, intent=None):
        pass

    def get_visual_data(self):
        from models.model_state import ModelVisualData
        return ModelVisualData(
            x=self.rect.x, y=self.rect.y,
            width=self.rect.width, height=self.rect.height,
            vel_x=self.vel_x, vel_y=self.vel_y,
            on_ground=self.on_ground, facing_left=self.facing_left,
            is_dead=self.is_dead, anim_hint='idle',
        )


def make_char(config=None):
    return DummyCharacter(0, 0, 32, 48, config=config)


class FakeDeathBehavior:
    def __init__(self):
        self.died = 0
        self.updated = 0

    def attach(self, owner):
        self.owner = owner

    def die(self, launch_up):
        self.died += 1

    def update(self, dt):
        self.updated += 1
        return True  # считаем завершённым


class FakeRespawnBehavior:
    def __init__(self, result):
        self._result = result

    def attach(self, owner):
        self.owner = owner

    def spawn_copy(self):
        return self._result


def test_base_character_initial_state():
    c = make_char()
    assert c.vel_x == 0.0
    assert c.vel_y == 0.0
    assert c.on_ground is False
    assert c.facing_left is False
    assert c.is_dead is False
    assert c.physics is not None  # композиция с физикой создана


def test_base_character_has_physics_component():
    c = make_char()
    assert isinstance(c.physics, PhysicsComponent)


def test_apply_physics_proxies_to_component():
    c = make_char()
    result = c.apply_physics(0.016, [])
    # без платформ и гравитации -> головой не бьётся
    assert result in (True, False)  # bool от apply
    # позиция может немного сдвинуться из-за гравитации на 1 шаг
    assert isinstance(result, bool)


def test_die_sets_is_dead_and_calls_behavior():
    db = FakeDeathBehavior()
    c = DummyCharacter(0, 0, 32, 48, death_behavior=db)
    assert c.is_dead is False
    c.die(launch_up=True)
    assert c.is_dead is True
    assert db.died == 1


def test_die_is_idempotent():
    db = FakeDeathBehavior()
    c = DummyCharacter(0, 0, 32, 48, death_behavior=db)
    c.die()
    c.die()          # повторный вызов не должен усилить счётчик
    assert c.is_dead is True
    assert db.died == 1


def test_update_death_with_behavior():
    db = FakeDeathBehavior()
    c = DummyCharacter(0, 0, 32, 48, death_behavior=db)
    result = c.update_death(0.1)
    assert result is True        # поведение вернуло True (завершено)
    assert db.updated == 1


def test_update_death_without_behavior_returns_false():
    c = make_char()
    assert c.update_death(0.1) is False


def test_spawn_copy_without_respawn_returns_self():
    c = make_char()
    assert c.spawn_copy() is c


def test_spawn_copy_with_respawn_uses_behavior():
    copy = DummyCharacter(10, 10, 32, 48)
    rb = FakeRespawnBehavior(copy)
    c = DummyCharacter(0, 0, 32, 48, respawn_behavior=rb)
    assert c.spawn_copy() is copy