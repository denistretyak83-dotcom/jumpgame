"""PhysicsComponent -- отдельная логика движения и коллизий.

Вынесена из BaseCharacter (композиция вместо наследования).
Любая сущность может подключить физику, передав себя в apply().
Отвязан от конкретного класса: работает с entity.rect/vel_x/vel_y.
"""
from dataclasses import dataclass


@dataclass
class PhysicsConfig:
    """Параметры физики, извлекаемые из настроек."""
    gravity: float = 1500
    max_fall: float = 1400
    ground_tolerance: float = 8.0


class PhysicsComponent:
    def __init__(self, config=None):
        # config может быть PhysicsConfig или словарь с .player/.physics
        self._config = config or PhysicsConfig()
        self._gravity = self._extract_gravity()
        self._max_fall = self._extract_max_fall()

    # ------------------------------------------------------------------
    # Извлечение параметров из разных форм конфига
    # ------------------------------------------------------------------

    def _extract_gravity(self):
        c = self._config
        if isinstance(c, PhysicsConfig):
            return c.gravity
        # словарь вида {"physics": {"gravity": ...}} или объект с атрибутами
        try:
            return c.physics.gravity
        except AttributeError:
            try:
                return c["physics"]["gravity"]
            except (KeyError, TypeError):
                return 1500

    def _extract_max_fall(self):
        c = self._config
        if isinstance(c, PhysicsConfig):
            return c.max_fall
        try:
            return c.physics.max_fall
        except AttributeError:
            try:
                return c["physics"]["max_fall"]
            except (KeyError, TypeError):
                return 1400

    # ------------------------------------------------------------------
    # Главный метод: применить физику к сущности
    # ------------------------------------------------------------------

    def apply(self, entity, dt, platforms):
        """Применяет физику к сущности.

        Returns:
            bool: True, если произошёл "удар головой" о низ платформы
            (entity.vel_y был отрицательный вверх и ударился снизу).
        """
        head_bumped = False

        if entity.is_dead:
            return head_bumped
        if not hasattr(entity, 'rect'):
            return head_bumped

        # --- Гравитация ---
        if not entity.on_ground:
            entity.vel_y += self._gravity * dt
            if entity.vel_y > self._max_fall:
                entity.vel_y = self._max_fall

        # --- Вертикаль + коллизии ---
        entity.rect.y += int(entity.vel_y * dt)
        for p in platforms:
            if entity.rect.colliderect(p):
                if entity.vel_y > 0.5 and entity.rect.top < p.top:
                    entity.rect.bottom = p.top
                    entity.vel_y = 0
                    entity.on_ground = True
                elif entity.vel_y < -0.5 and entity.rect.top < p.bottom:
                    # ← УДАР ГОЛОВОЙ о низ платформы
                    entity.rect.top = p.bottom
                    entity.vel_y = 0
                    head_bumped = True  # ← отмечаем удар головой

        # --- Горизонталь + коллизии ---
        entity.rect.x += int(entity.vel_x * dt)
        for p in platforms:
            if entity.rect.colliderect(p):
                if entity.vel_x > 0:
                    entity.rect.right = p.left
                elif entity.vel_x < 0:
                    entity.rect.left = p.right

        self.update_grounded(entity, platforms)
        return head_bumped

    def update_grounded(self, entity, platforms):
        """Обновляет on_ground по касанию (с допуском, не строгий colliderect)."""
        tolerance = self._ground_tolerance()
        grounded = False
        for p in platforms:
            if (entity.rect.bottom >= p.top - 1
                    and entity.rect.bottom <= p.top + tolerance
                    and entity.rect.bottom > p.top - 2
                    and entity.vel_y >= -0.5):
                if entity.rect.right > p.left and entity.rect.left < p.right:
                    grounded = True
                    break
        entity.on_ground = grounded

    def _ground_tolerance(self):
        return self._config.ground_tolerance if isinstance(self._config, PhysicsConfig) else 8.0