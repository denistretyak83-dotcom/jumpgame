# Аудит исходного кода «Jump & Reach the Flag» — редакция v3

**Анализируемый артефакт:** JumpGame (Python + pygame, MVC-архитектура).
**Метод:** статический анализ актуального кода + факты из SESSION_CHECKPOINT.md
(312 тестов, CI-пайплайн).
**Дата:** после завершения Фаз 7–11.
---

## 0.1. Резюме изменений относительно v2 (Фазы 8–10)

> v2 фиксировала состояние после Фазы 7 (297 тестов). Затем закрыты три фазы дорожной карты.

| Было в v2 | Стало теперь | Статус |
|---|---|---|
| ⚠️ Мёртвые `enemy_controller.py`, `player_view.py` | Удалены | ✅ Закрыто |
| ⚠️ Мёртвый `Game._respawn_player()` | Удалён (дубль PlayerFlow) | ✅ Закрыто |
| ⚠️ Lambda-реестр вью Player/Enemy в `Game.__init__` | Вынесен в `views/view_factory.py` (OCP) | ✅ Закрыто |
| ⚠️ Хардкод цветов монет/иконки | Вынесен в `config.colors` + `views/coin_icon.py` | ✅ Закрыто |
| Тестов: 297 | **312 passed** | ✅ Рост на 15 |

Новые файлы: `views/view_factory.py`, `views/coin_icon.py`.
Новые тесты: `tests/test_view_factory.py` (+5), `tests/test_theme.py` (+3),
`test_geometry.py` (+3), `test_collision_system.py` (+2), `test_physics.py` (+1),
`test_entity.py` (+1).

### 0.2. Фаза 11 — риск №1 снят (в дополнение к 0.1)
- Риск №1 (pygame.Rect в моделях) оказался уже внедрённым (Фаза 4: `core/geometry.RectPosition`).
  Фаза 11 провела аудит покрытия и закрыла пробелы.
- Устранён дефект: `CollisionSystem.check` бросал IndexError, если `coin_collected`
  короче `coins` — добавлена защита по длине.
---

## 1. Аудит по осям

### a) Структура и слои

**Соответствует.**

Пакеты чистые: `core/ models/ views/ controllers/ levels/ audio/ main.py`. Точка входа тонкая.
Мёртвые модули (`enemy_controller.py`, `player_view.py`) удалены в Фазе 8 — дерево чистое.

### b) SOLID

#### S — Single Responsibility

**Значительно улучшено.** `Game` больше не God-Object:
- смерть/жизни/респавн → `PlayerFlow`;
- каталог/переходы уровней → `LevelTransition`;
- game-over фейд и рестарт → `GameOverHandler`;
- коллизии и игровые правила → `CollisionDirector`.

Остаточные обязанности в `Game`:
- роль **фабрики/композиции** — `__init__` создаёт окно, шрифты, `view_registry`, системы;
- в __init__ собирает окно, шрифты и передаёт реестр вью из `ViewFactory`;
  мёртвый `_respawn_player()` удалён в Фазе 8.
`Entity` больше не God-класс геометрии в старом смысле: равботает на
`core.geometry.RectPosition` (Фаза 4), а не на `pygame.Rect`; риск №1 снят в Фазе 11.
#### O — Open/Closed

**Хорошо.** `WorldFactory` registry, `EnemyBehaviorRegistry`, `Renderer.view_registry` + `register_view`.
С Фазы 9 реестр вью Player/Enemy строится в `views/view_factory.py` (единый `ViewFactory`),
а `Game` и Composition Root получают его готовым — OCP-точка больше не в оркестраторе.
#### L — Liskov

Базовая композиция поведений и состояний снижает необходимость в подстановке. `Player`/`Enemy` взаимозаменяемы в цикле `entity.update(dt, ctx, intent)` и в `draw_entities` через `get_visual_data()`.

#### I — Interface Segregation

**Частично.** Есть `Collidable`, `Animatable` (Protocol). Замечания:
- `Animatable` объявлен, но **не используется**;
- `PlayableCharacter` отсутствует (ожидаемая будущая работа).

#### D — Dependency Inversion

Открытая проблема была: `controllers/enemy_controller.py` ссылался на несуществующий
`settings` (потенциальный ImportError). Фаза 8 удалила модуль — мина снята.
### c) MVC

**Соответствует ядру.**
- Model → DTO: `get_visual_data()` → `ModelVisualData` (без pygame).
- View через DTO: `Renderer.draw_entities` → `_view_for` → `CharacterView.build_state` → `render`.
- Controller — единственный читатель ввода: `PlayerController` (keys → `PlayerIntent`).
- Игровые правила вынесены в `CollisionDirector`, а не лежат в `Game`.

### d) EventBus (Observer)

**Полностью соответствует.** Токенизированная подписка, изоляция ошибок в `emit()`, константы `GameEvents.*`.

### e) Data-Driven уровни

**Соответствует, с нюансом JSON-схемы.** JSON → `LevelBuilder` → фабрики. Враги задаются `{behavior, sprite}` с fallback на `config.enemy`. В данных нет персональных `width/height/speed` врагов, что расходится с ранней декларацией и README.

### f) State machine игрока

**Полностью соответствует.** `PlayerState` (ABC) + `Idle/Run/Jump/Fall` + `PlayerStateMachine`.

### g) Конвенция зарезервированных properties

**Соблюдена.** `bound_left/right`, `pos_x/pos_y`; нарушений не найдено.

### h) Риски-реалии

| Риск | Статус |
|---|---|
| 1. Модели зависят от `pygame.Rect` | ✅ **Снят** (`Entity` на `RectPosition`; pygame.Rect только в View через `to_pygame_rect`) |
| 2. Game как God-Object | ✅ **Снят** (декомпозирован) |
| 3. Enemy без физики/гравитации | ⚠️ Актуален (`apply_physics` только у Player) — Фаза 12 |
| 4. Физика пишет в rect напрямую | ✅ Подтверждён (осознанно) |

### i) Качество кода

- ✅ Хардкод цветов монет/иконки вынесен в `config.colors` (Фаза 10);
  остаточный хардкод (при его наличии) — в `background.py`/`hud.py`.
- ✅ Типизация, docstrings, типизированные `try/except`.
- ✅ 312 тестов + CI-пайплайн.
- ⚠️ `Game.__init__` — масштабная фабричная композиция (много ответственности сборки).
---

## 2. Обновлённая оценка

## 2. Обновлённая оценка

**v1:** ≈ 6,5/10.
**v2:** ≈ 8,5/10.
**v3:** ≈ 9,0/10.
**v4 (текущая):** ≈ **9,2/10**.

Обоснование: Фазы 8–11 закрыты — мёртвый код удалён (Фаза 8), OCP-регистрация вью
изолирована (Фаза 9), цвета централизованы (Фаза 10), риск №1 (pygame.Rect) снят
и покрытие геометрии/физики/коллизий доведено, устранён дефект `coin_collected` (Фаза 11).
312 тестов.

До 9,5–10 не дотягивает из-за: риска №3 (Enemy без физики, Фаза 12), неиспользуемого
`Animatable` Protocol и рассинхрона README/JSON (Фаза 13).
---

## 3. Актуальные нарушения (с приоритетом)

**Критично:**
— (пусто) — мины ImportError и дефект `coin_collected` закрыты.

**Важно:**
- Риск №3 — Enemy без физики/гравитации (Фаза 12).
- `Animatable` Protocol объявлен, но не используется (мелкий долг).

**Незначительно:**
- Рассинхрон README/JSON (персональные данные врагов) — Фаза 13.
- Массовая композиция в `Game.__init__` (уже ослаблена Фазами 7–9).
---

## 4 План улучшений
> Каждая фаза сохраняет зелёный прогон тестов (текущая база — 312) и добавляет новые.

### Фаза 8 — Гигиена мёртвого кода [DONE]
- ✅ 8.1 Удалить `controllers/enemy_controller.py`.
- ✅ 8.2 Удалить `views/player_view.py`.
- ✅ 8.3 Удалить `Game._respawn_player()`.
- Коммит: `chore: remove dead modules`.

### Фаза 9 — Изоляция OCP-регистрации вью от Game [DONE]
- ✅ 9.1 Перенесено в `views/view_factory.py`.
- ✅ 9.2 `Renderer.set_view_registry()`; Game не строит lambda Player/Enemy.
- ✅ Тест: `tests/test_view_factory.py` (+5).

### Фаза 10 — Вынос констант/цветов (R5/Theme) [DONE]
- ✅ 10.1 Цвета монет/иконки в `config.colors`.
- ✅ 10.2 `Renderer._color()` с fallback; `views/coin_icon.py`.
- ✅ Тест: `tests/test_theme.py` (+3) — smoke-рендер не изменился.

### Фаза 11 — Геометрия/коллизии (риск №1) [DONE]
- ✅ Риск №1 снят (реезация уже была в Фазе 4: `core/geometry.RectPosition`).
- ✅ Аудит покрытия: `test_geometry.py` (+3), `test_entity.py` (+1),
  `test_physics.py` (+1), `test_collision_system.py` (+2).
- ✅ Дефект: защита `CollisionSystem.check` от IndexError при `coin_collected < coins`.

### Фаза 12 — Расширяемость героев и врагов
- Ввести `PlayableCharacter` Protocol/ABC; `Player` реализует контракт.
- `EnemyBehavior` registry — добавить новый тип без правки логики.
- Обсудить физику для Enemy (гравитация) — риск №3.

### Фаза 13 — Инфраструктура качества
- Линтеры (ruff/black/isort) + типизация (mypy/pyright) в `ci.yml`.
- `pytest --cov` (порог покрытия моделей).
- Согласовать README с JSON-схемой врагов.

---

## 5. Рекомендуемый старт

Фазы 8–11 закрыты. Дальше — **Фаза 12** (расширяемость героев и врагов):
ввести `PlayableCharacter` Protocol/ABC (Player реализует контракт), расширить
`EnemyBehavior` registry новым типом, обсудить физику Enemy (риск №3).

