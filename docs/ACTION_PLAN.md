# ACTION_PLAN — «Jump & Reach the Flag» (план действий)

Обновлён по итогам выполнения Фаз 0-3.

## Статус фаз
| Фаза | Название | Статус |
|---|---|---|
| 0 | Санитизация | ✅ |
| 1 | Инфраструктура качества (CI, ruff, pytest, coverage, release) | ✅ |
| 2 | Тестовый фундамент (покрытие 81,7%, 202 теста) | ✅ |
| 3 | Декомпозиция Game (CollisionDirector, LevelFlow, PhysicsProtocol, DIP) | ✅ |
| 4 | Отказ от pygame.Rect + прочистка геометрии | ⏳ СЛЕДУЮЩАЯ |
| 5 | Data-Driven расширение (враги в2-в4, платформы, JSON) | ⏳ |
| 6 | Продуктовые фичи (герои, Theme, редактор, блоки) | ⏳ |

## Приоритеты: P0 (высокий), P1 (средний), P2 (низкий)

## Завершённые задачи (детали)
- G1 CI/CD, G2 линтеры/форматтеры, G3 покрытие >=80% — выполнены (Фаза 1-2).
- 4.3 устранение дублей + Protocol физики — выполнено.
- 4.4 юнит-тесты (Entity, CollisionSystem, Enemy, Physics) — выполнено.
- 4.7 тесты Game до выноса — выполнено (CollisionDirector, LevelFlow).
- 4.2/4.6 декомпозиция Game (CollisionDirector/LevelFlow + DIP) — выполнено большинство.
- 4.8 DIP-схема — задокументирована (docs/DIP.md).

## Следующая фаза: Фаза 4 «Отказ от pygame.Rect» (P0)
Задачи:
- 4.5: Прочистка Entity — вынести 9 properties-геометрию в отдельный Geometry/RectPosition; Entity — только сущностные данные.
- 4.1: Собственный dataclass RectPosition в core/geometry.py (без pygame); to_pygame_rect().
- Затрагивает PhysicsComponent, CollisionSystem, Renderer/CharacterView, Camera, Game.
- Под юнит-тестами (геометрия, коллизии) перед применением.
- Контракт: физика пишет в rect / владелец float-источника не в цикле физики.

## После Фазы 4
- Фаза 5: враги в2 (EnemyBehavior по типу), в3 (View по типу/размеру), в4 (физика/летающие); платформы-типы (C); стабилизация JSON-схемы (I1 + мигратор); каталог уровней (J2).
- Фаза 6: герои (B), Theme/Skin (D+J1), редактор (E), разрушаемые блоки + AttackState (F), валидатор (I2), data-контракт (I3).
- Вернуть views/audio к покрытию после стабилизации SOLID/MVC/OCP.

## DoD (общие)
Тесты зелёные, ruff clean, format clean, coverage >=80% по scope, CI зелёный,
OCP-регистрация, события через GameEvents.*, конвенции имён, игра работает.

## Быстрые шаги после возврата в сессию
1. pytest, ruff, coverage — сверить зелёные.
2. Приступить к Фазе 4: начать с core/geometry.py (RectPosition) + тесты геометрии.
3. Затем прочистка Entity (4.5) и отказ от rect в моделях (4.1).