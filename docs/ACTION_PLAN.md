# ACTION_PLAN — «Jump & Reach the Flag» (план действий)

Обновлён по итогам выполнения Фаз 0-4.

## Статус фаз
| Фаза | Название | Статус |
|---|---|---|
| 0 | Санитизация | ✅ |
| 1 | Инфраструктура качества (CI, ruff, pytest, coverage, release) | ✅ |
| 2 | Тестовый фундамент (покрытие 81,7%, 202 теста) | ✅ |
| 3 | Декомпозиция Game (CollisionDirector, LevelFlow, PhysicsProtocol, DIP) | ✅ |
| 4 | Отказ от pygame.Rect + прочистка геометрии | ✅ (226 тестов, покрытие ~82,8%) |
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
- 4.5 Прочистка Entity — вынесена геометрия в RectPosition; Entity хранит только сущностные данные — выполнено.
- 4.1 Собственный RectPosition в core/geometry.py (без pygame) — выполнено; миграция PhysicsComponent, CollisionSystem, Factory, LevelManager.

## Фаза 4 «Отказ от pygame.Rect» (P0) — ВЫПОЛНЕНА
- 4.5 Прочистка Entity: внутренний rect → RectPosition; убран `import pygame`; добавлен to_pygame_rect() (для View/рендера); 9 геометрия-properties сохранены (контракт не изменён).
- 4.1 Собственный dataclass RectPosition в core/geometry.py (без pygame): геттеры/сеттеры left/top/right/bottom/centerx/centery + intersects(), colliderect(), move(), move_ip(), copy(), contains_point(), to_pygame_rect().
- Мигрированы: PhysicsComponent, CollisionSystem, Factory, LevelManager (pygame.Rect → RectPosition).
- Renderer (views) строит pygame.Rect по требованию через to_pygame_rect() — корректно по DIP.
- Тесты переведены на pygame-независимую геометрию.
- Итог: 226 passed (было 202), coverage ~82,8% (≥80%), ruff clean, format clean, py_compile 67 файлов OK. Игра работает.

## Следующая фаза: Фаза 5 «Data-Driven расширение» (P0)
Задачи:
- Враги в2: поведение по типу (реестр behaviors); в3: View по типу/размеру; в4: физика/летающие.
- Платформы-типы (C): типизированные платформы через WorldFactory (OCP).
- Стабилизация JSON-схемы (I1 + мигратор); каталог уровней (J2).
- Контракты сохранены: DI через конструктор, события через GameEvents.*, никаких глобалов/синглтонов/import settings, конвенции имён.

## После Фазы 5
- Фаза 6: герои (B), Theme/Skin (D+J1), редактор (E), разрушаемые блоки + AttackState (F), валидатор (I2), data-контракт (I3).
- Вернуть views/audio к покрытию после стабилизации SOLID/MVC/OCP.

## DoD (общие)
Тесты зелёные, ruff clean, format clean, coverage >=80% по scope, CI зелёный,
OCP-регистрация, события через GameEvents.*, конвенции имён, игра работает.

## Быстрые шаги после возврата в сессию
1. pytest, ruff, coverage — сверить зелёные (226 passed, coverage ~82,8%).
2. Перейти к Фазе 5 (Data-Driven расширение) по приоритетам выше.
3. Позже — вернуть views/audio к покрытию и Фаза 6.