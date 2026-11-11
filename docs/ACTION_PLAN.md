# ACTION_PLAN — «Jump & Reach the Flag» (план действий)

Обновлён по итогам выполнения Фаз 0-4.

## Статус фаз
| Фаза | Название | Статус |
|---|---|---|
| 0 | Санитизация | ✅ |
| 1 | Инфраструктура качества (CI, ruff, pytest, coverage, release) | ✅ |
| 2 | Тестовый фундамент (покрытие 81,7%, 202 теста) | ✅ |
| 3 | Декомпозиция Game (CollisionDirector, LevelFlow, PhysicsProtocol, DIP) | ✅ |
| 4 | Отказ от pygame.Rect + прочистка геометрии | ✅ (226 тестов, покрытие 82,8%) |
| 5 | Data-Driven расширение (враги в2-в4, платформы, JSON) | ⏳ СЛЕДУЮЩАЯ |
| 6 | Продуктовые фичи (герои, Theme, редактор, блоки) | ⏳ |

## Приоритеты: P0 (высокий), P1 (средний), P2 (низкий)

## Завершённые задачи (детали)
- G1 CI/CD, G2 линтеры/форматтеры, G3 покрытие >=80% — выполнены (Фаза 1-2).
- 4.3 устранение дублей + Protocol физики — выполнено.
- 4.4 юнит-тесты (Entity, CollisionSystem, Enemy, Physics) — выполнено.
- 4.7 тесты Game до выноса — выполнено (CollisionDirector, LevelFlow).
- 4.2/4.6 декомпозиция Game (CollisionDirector/LevelFlow + DIP) — выполнено большинство.
- 4.8 DIP-схема — задокументирована (docs/DIP.md).

## Фаза 4 «Отказ от pygame.Rect» (P0) — ВЫПОЛНЕНА
### 4.5 — Прочистка Entity
- `models/entity.py`: внутренний `pygame.Rect` заменён на `RectPosition` из `core/geometry.py`.
  - `import pygame` убран; добавлен `to_pygame_rect()` для View/рендера.
  - 9 properties (x, y, width, height, left, top, right, bottom, centerx, centery) сохранены и делегируют в `self.rect` — публичный контракт не изменён.
- `core/geometry.py`: `RectPosition` дополнен сеттерами `left/top/right/bottom/centerx/centery`,
  методом `colliderect()` (алиас `intersects()`), `move()`, `move_ip()`.
- `tests/test_geometry.py` расширен: bounds-сеттеры, пересечения по краям/осям,
  negative coords, float-точность, алиас colliderect, contains_point границы.

### 4.1 — Отказ от pygame.Rect в моделях
- `models/physics.py`: `PhysicsBody.rect -> RectPosition`; `colliderect` → `RectPosition.intersects()`;
  используются свойства `bottom/top/right/left`. Контракт сохранён (физика пишет в rect,
  владелец float-источника `enemy.pos_x/pos_y` вне цикла физики; `int()` при записи — нет дёрганий).
- `models/collision_system.py`: `Collidable.rect -> RectPosition`; `check()` принимает/возвращает RectPosition;
  `colliderect` → `intersects()`.
- `models/factory.py`: `_build_rect()` возвращает `RectPosition` вместо `pygame.Rect`.
- `levels/level_manager.py`: типы `platforms/coins/flag_rect` → `RectPosition`.
- `core/game.py`, `core/level_flow.py`, `core/gameplay.py`: работают через `player.rect` (свойства сохранены).
- View (`views/*`) остались на pygame.Rect (строят его из DTO/через `to_pygame_rect()`) — корректно по DIP.

### Миграция тестов под Фазу 4
- `test_entity.py`, `test_physics.py`, `test_collision_system.py`, `test_enemy_behavior.py`
  переведены с `pygame.Rect` на `RectPosition`; убран `skipif(нужен pygame.Rect)`.

## Следующая фаза: Фаза 5 «Data-Driven расширение» (P0)
- Враги в2 (EnemyBehavior по типу), в3 (View по типу/размеру), в4 (физика/летающие); платформы-типы (C);
  стабилизация JSON-схемы (I1 + мигратор); каталог уровней (J2).

## После Фазы 5
- Фаза 6: герои (B), Theme/Skin (D+J1), редактор (E), разрушаемые блоки + AttackState (F), валидатор (I2), data-контракт (I3).
- Вернуть views/audio к покрытию после стабилизации SOLID/MVC/OCP.

## DoD (общие)
Тесты зелёные, ruff clean, format clean, coverage >=80% по scope, CI зелёный,
OCP-регистрация, события через GameEvents.*, конвенции имён, игра работает.

## Быстрые шаги после возврата в сессию
1. pytest, ruff, coverage — сверить зелёные.
2. Продолжить Фазу 5 (Data-Driven расширение) по пунктам ACTION_PLAN.