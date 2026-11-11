"""PhysicsComponent -- отдельная логика движения и коллизий.

Вынесена из BaseCharacter (композиция вместо наследования).
Любая сущность может подключить физику, передав себя в apply().
Отвязан от конкретного класса: работает с entity.rect/vel_x/vel_y.

Фаза 4 (4.1): модели работают с core.geometry.RectPosition вместо pygame.Rect.
Физика пишет в entity.rect (RectPosition); сам rect больше НЕ pygame.Rect.

Внимание (п.7 мемо): локальный dataclass переименован из PhysicsConfig в
PhysicsParams, чтобы устранить дубль имени с официальным
core.config.PhysicsConfig (публичный конфиг из settings.json).
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.geometry import RectPosition


@runtime_checkable
class PhysicsBody(Protocol):
    """Что сущность обязана предоставлять, чтобы физика могла её двигать.

    Контракт физики (DIP): PhysicsComponent работает только с этим
    интерфейсом, а не с конкретным классом (Player/Enemy/BaseCharacter).
    """

    rect: RectPosition
    vel_x: float
    vel_y: float
    on_ground: bool
    is_dead: bool


@runtime_checkable
class PhysicsEngine(Protocol):
    """Интерфейс компонента физики, который ожидает владелец сущности.

    Позволяет подменять реализацию физики (например, для тестов или
    других схем движения) без изменения BaseCharacter.
    """

    def apply(self, entity: PhysicsBody, dt: float, platforms) -> bool:
        """Применить физику; True — удар головой."""
        ...

    def update_grounded(self, entity: PhysicsBody, platforms) -> None:
        """Обновить флаг on_ground по касанию платформ."""
        ...


@dataclass
class PhysicsParams:
    """Внутренние параметры физики (fallback-значения компонента)."""

    gravity: float = 1500
    max_fall: float = 1400
    ground_tolerance: float = 8.0


class PhysicsComponent:
    def __init__(self, config=None):
        self._config = config if config is not None else PhysicsParams()
        self._gravity = self._resolve_gravity()
        self._max_fall = self._resolve_max_fall()
        self._ground_tolerance = self._resolve_ground_tolerance()

    def _resolve_gravity(self):
        cfg = self._config
        if isinstance(cfg, PhysicsParams):
            return cfg.gravity
        physics = getattr(cfg, "physics", None)
        if physics is not None:
            return getattr(physics, "gravity", PhysicsParams.gravity)
        return PhysicsParams.gravity

    def _resolve_max_fall(self):
        cfg = self._config
        if isinstance(cfg, PhysicsParams):
            return cfg.max_fall
        physics = getattr(cfg, "physics", None)
        if physics is not None:
            return getattr(physics, "max_fall", PhysicsParams.max_fall)
        return PhysicsParams.max_fall

    def _resolve_ground_tolerance(self):
        cfg = self._config
        if isinstance(cfg, PhysicsParams):
            return cfg.ground_tolerance
        # У core.config.physics нет ground_tolerance -> внутренний дефолт
        return PhysicsParams.ground_tolerance

    def apply(self, entity, dt, platforms):
        """Применяет физику к сущности. True — удар головой."""
        head_bumped = False
        if entity.is_dead:
            return head_bumped
        if not hasattr(entity, "rect"):
            return head_bumped

        if not entity.on_ground:
            entity.vel_y += self._gravity * dt
            if entity.vel_y > self._max_fall:
                entity.vel_y = self._max_fall

        entity.rect.y += int(entity.vel_y * dt)
        for p in platforms:
            if entity.rect.intersects(p):
                if entity.vel_y > 0.5 and entity.rect.top < p.top:
                    entity.rect.bottom = p.top
                    entity.vel_y = 0
                    entity.on_ground = True
                elif entity.vel_y < -0.5 and entity.rect.top < p.bottom:
                    entity.rect.top = p.bottom
                    entity.vel_y = 0
                    head_bumped = True

        entity.rect.x += int(entity.vel_x * dt)
        for p in platforms:
            if entity.rect.intersects(p):
                if entity.vel_x > 0:
                    entity.rect.right = p.left
                elif entity.vel_x < 0:
                    entity.rect.left = p.right

        self.update_grounded(entity, platforms)
        return head_bumped

    def update_grounded(self, entity, platforms):
        """Обновляет on_ground по касанию (с допуском)."""
        tolerance = self._ground_tolerance
        grounded = False
        for p in platforms:
            if (
                entity.rect.bottom >= p.top - 1
                and entity.rect.bottom <= p.top + tolerance
                and entity.rect.bottom > p.top - 2
                and entity.vel_y >= -0.5
                and entity.rect.right > p.left
                and entity.rect.left < p.right
            ):
                grounded = True
                break
        entity.on_ground = grounded
