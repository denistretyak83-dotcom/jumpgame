"""enemy_behaviors_extra.py — дополнительные OCP-поведения врагов (Фаза 12).

ZigzagBehavior — образец расширяемости реестра EnemyBehaviorRegistry:
новый тип добавляется одной регистрацией (register("zigzag", ZigzagBehavior))
БЕЗ правки логики Enemy или существующих поведений.
"""

from models.enemy_behavior import EnemyBehavior


class ZigzagBehavior(EnemyBehavior):
    """Зигзаг: X-патруль (как Walker/Chaser) + рывки по Y.

    Движется вправо-влево между bound_left/bound_right, а по Y совершает
    резкие рывки вверх/вниз с фиксированной скоростью. Гравитацию и
    платформы игнорирует (как Flyer/Jumper) — движение задаётся напрямую.

    Синхронизирует rect.x и rect.y из float-источников pos_x/pos_y.
    """

    def __init__(self, zig_speed: float = 80.0, zig_range: float = 40.0):
        self._enemy = None
        self.zig_speed = zig_speed
        self.zig_range = zig_range
        self._y_dir = 1

    def attach(self, enemy) -> None:
        self._enemy = enemy
        self._base_y = float(enemy.rect.y)
        enemy.pos_y = float(enemy.rect.y)
        self._y_dir = 1

    def update(self, enemy, dt, ctx=None, intent=None) -> None:
        # --- X-движение (патруль) ---
        pos_x = enemy.pos_x + enemy.vel_x * dt
        if pos_x < enemy.bound_left:
            overrun = enemy.bound_left - pos_x
            pos_x = enemy.bound_left + overrun
            enemy.vel_x = abs(enemy.vel_x)
        elif pos_x + enemy.rect.width > enemy.bound_right:
            overrun = (pos_x + enemy.rect.width) - enemy.bound_right
            pos_x = enemy.bound_right - enemy.rect.width - overrun
            enemy.vel_x = -abs(enemy.vel_x)

        # --- Y-движение: отслеживаем текущую базовую позицию ---
        # Если враг не хранит pos_y (как base-walker), используем rect.y.
        cur_y = float(enemy.pos_y) if hasattr(enemy, "pos_y") else float(enemy.rect.y)
        next_y = cur_y + self._y_dir * self.zig_speed * dt
        if next_y > self._base_y + self.zig_range:
            self._y_dir = -1
            next_y = self._base_y + self.zig_range
        elif next_y < self._base_y - self.zig_range:
            self._y_dir = 1
            next_y = self._base_y - self.zig_range

        # --- Синхронизация rect из float-позиции ---
        enemy.pos_x = pos_x
        enemy.pos_y = next_y
        enemy.rect.x = int(round(enemy.pos_x))
        enemy.rect.y = int(round(next_y))
