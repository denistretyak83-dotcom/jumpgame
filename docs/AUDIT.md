# Аудит исходного кода «Jump & Reach the Flag» — редакция v2

**Анализируемый артефакт:** JumpGame (Python + pygame, MVC-архитектура).
**Метод:** статический анализ актуального кода (`core/game.py`, `core/gameplay.py`, `views/renderer.py`, `main.py`) + факты из `SESSION_CHECKPOINT.md` (297 тестов, CI-пайплайн).
**Дата:** после завершения Фазы 7.

---

## 0. Резюме изменений относительно редакции v1

> v1 фиксировала состояние ДО Фазы 7. За это время закрыты ключевые пункты декомпозиции и качества.

| Было в v1 | Стало теперь | Статус |
|---|---|---|
| ❌ Ноль юнит-тестов | **297 passed** | ✅ Закрыто |
| ❌ `Game` — God-Object (вся логика в `_update`) | `PlayerFlow`, `LevelTransition`, `GameOverHandler`, `CollisionDirector` вынесены | ✅ Закрыто |
| ❌ Коллизии/игровые правила в `Game` | Правила в `CollisionDirector.process` | ✅ Закрыто |
| ❌ Нет DI (кроме `config`/`logger`) | DIP через `services` + Composition Root в `main.py` | ✅ Закрыто |
| ⚠️ `Renderer.draw` — fat-interface (~12 арг.) | `draw(state: RenderState)` — data-class | ✅ Закрыто |
| ⚠️ `models/collision.py` — дубликат + магия `30` | удалён | ✅ Закрыто |
| ❌ Нет CI | `.github/workflows/ci.yml` + `release.yml` | ✅ Закрыто |
| ❌ Мёртвые файлы `enemy_controller.py`, `player_view.py` | остались на месте | ⚠️ Открыто |

---

## 1. Аудит по осям

### a) Структура и слои

**Соответствует, с двумя мёртвыми файлами.**

Пакеты чистые: `core/ models/ views/ controllers/ levels/ audio/ main.py`. Точка входа тонкая. В дереве остаются два неиспользуемых модуля, не предусмотренных текущей архитектурой:
- `controllers/enemy_controller.py`;
- `views/player_view.py`.

### b) SOLID

#### S — Single Responsibility

**Значительно улучшено.** `Game` больше не God-Object:
- смерть/жизни/респавн → `PlayerFlow`;
- каталог/переходы уровней → `LevelTransition`;
- game-over фейд и рестарт → `GameOverHandler`;
- коллизии и игровые правила → `CollisionDirector`.

Остаточные обязанности в `Game`:
- роль **фабрики/композиции** — `__init__` создаёт окно, шрифты, `view_registry`, системы;
- **мёртвый метод `_respawn_player()`** — дублирует `PlayerFlow.respawn` и в `_update` не вызывается.

`Entity` остаётся **God-классом геометрии** (9+ properties → `pygame.Rect`) — риск №1 не решён.

#### O — Open/Closed

**Хорошо.** `WorldFactory` registry, `EnemyBehaviorRegistry`, `Renderer.view_registry` + `register_view`. Замечание: регистрация вью для Player/Enemy строится **lambda-фабриками прямо в `Game.__init__`** — OCP-точка остаётся в оркестраторе, а не в `SpriteCache`/фабрике вью.

#### L — Liskov

Базовая композиция поведений и состояний снижает необходимость в подстановке. `Player`/`Enemy` взаимозаменяемы в цикле `entity.update(dt, ctx, intent)` и в `draw_entities` через `get_visual_data()`.

#### I — Interface Segregation

**Частично.** Есть `Collidable`, `Animatable` (Protocol). Замечания:
- `Animatable` объявлен, но **не используется**;
- `PlayableCharacter` отсутствует (ожидаемая будущая работа).

#### D — Dependency Inversion

**Значительно улучшено.** `Game(services=...)`, Composition Root в `main.py`.

Открытая проблема: **`controllers/enemy_controller.py` ссылается на несуществующий глобальный `settings`** (`from core.config import settings`) — при импорте был бы `ImportError`. Модуль мёртв, но код — потенциальная мина.

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
| 1. Модели зависят от `pygame.Rect` | ✅ Подтверждён (`Entity.rect`) |
| 2. Game как God-Object | ✅ **Снят** (декомпозирован) |
| 3. Enemy без физики/гравитации | ✅ Подтверждён (`apply_physics` только у Player) |
| 4. Физика пишет в rect напрямую | ✅ Подтверждён (осознанно) |

### i) Качество кода

- ⚠️ Хардкод цветов в `Renderer.draw` (монета/флаг), вероятно, в `background.py`/`hud.py` — вместо `config.colors`.
- ✅ Типизация, docstrings, типизированные `try/except`.
- ✅ 297 тестов + CI-пайплайн.
- ⚠️ `Game.__init__` — масштабная фабричная композиция (много ответственности сборки).

---

## 2. Обновлённая оценка

**v1:** ≈ 6,5/10.
**v2 (текущая):** ≈ **8,5/10**.

Обоснование: закрыты пять шагов Фазы 7 (SRP-декомпозиция Game, DIP, RenderState), 297 тестов, CI, удалён `collision.py`. До 9–9,5 не дотягивает из-за: мёртвых файлов (`enemy_controller`, `player_view`), мёртвого `Game._respawn_player`, lambda-реестра вью в Game, хардкода цветов, нерешённых рисков pygame.Rect и Enemy без физики.

---

## 3. Актуальные нарушения (с приоритетом)

**Критично:**
1. `controllers/enemy_controller.py` — ссылка на несуществующий глобальный `settings` (потенциальный `ImportError`). Модуль мёртв.

**Важно:**
2. `views/player_view.py` — мёртвый; читает несуществующие `player.animations` (нарушение «View не читает модель»).
3. `Game._respawn_player()` — мёртвый метод-дубль `PlayerFlow.respawn`.
4. OCP-регистрация вью (lambda Player/Enemy) в `Game.__init__` — размазана по оркестратору.
5. Хардкод цветов в рендере/фоне/HUD вместо `config.colors`.
6. Риск №1 — `Entity` + `pygame.Rect` (крупный, возможно отдельной фазой).

**Незначительно:**
7. Рассинхрон README/JSON (персональные данные врагов).
8. Массовая композиция в `Game.__init__`.

---

## 4. План улучшений (ООП/MVC/SOLID/расширяемость)

> Каждая фаза сохраняет зелёный прогон тестов (база 297) и добавляет новые.

### Фаза 8 — Гигиена мёртвого кода
- **8.1** Удалить `controllers/enemy_controller.py`.
- **8.2** Удалить `views/player_view.py`.
- **8.3** Удалить `Game._respawn_player()` (дубль `PlayerFlow.respawn`).
- Коммит: `chore: remove dead modules (enemy_controller, player_view, Game._respawn_player)`.

### Фаза 9 — Изоляция OCP-регистрации вью от Game
- **9.1** Перенести построение/регистрацию `view_registry` в `SpriteCache` (или фабрику вью).
- **9.2** `Renderer` принимает готовый реестр; `Game` не строит lambda Player/Enemy.
- Тест: отрисовка Player/Enemy по реестру.

### Фаза 10 — Вынос констант/цветов (R5/Theme)
- **10.1** Вынести цвета монеты/флага/фона/HUD в `config.colors` (или `config/theme.json`).
- **10.2** Протянуть цвета через `RenderState`/`Renderer`/HUD из конфига.
- Тест: smoke-рендер не изменился.

### Фаза 11 — Отделение геометрии от `pygame.Rect` (риск №1)
- Ввести `RectPosition`/`Geometry` DTO; `to_pygame_rect()` по требованию в View.
- Требуется полный набор тестов геометрии/коллизий до начала.

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

**Фаза 8** — удаление мёртвого кода: дёшево, чистит слои и убирает мину `ImportError`.

---

