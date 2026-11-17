# Аудит исходного кода «Jump & Reach the Flag» — редакция v3

**Анализируемый артефакт:** JumpGame (Python + pygame, MVC-архитектура).
**Метод:** статический анализ актуального кода + факты из SESSION_CHECKPOINT.md
(305 тестов, CI-пайплайн).
**Дата:** после завершения Фаз 7–10.
---

## 0.1. Резюме изменений относительно v2 (Фазы 8–10)

> v2 фиксировала состояние после Фазы 7 (297 тестов). Затем закрыты три фазы дорожной карты.

| Было в v2 | Стало теперь | Статус |
|---|---|---|
| ⚠️ Мёртвые `enemy_controller.py`, `player_view.py` | Удалены | ✅ Закрыто |
| ⚠️ Мёртвый `Game._respawn_player()` | Удалён (дубль PlayerFlow) | ✅ Закрыто |
| ⚠️ Lambda-реестр вью Player/Enemy в `Game.__init__` | Вынесен в `views/view_factory.py` (OCP) | ✅ Закрыто |
| ⚠️ Хардкод цветов монет/иконки | Вынесен в `config.colors` + `views/coin_icon.py` | ✅ Закрыто |
| Тестов: 297 | **305 passed** | ✅ Рост на 8 |

Новые файлы: `views/view_factory.py`, `views/coin_icon.py`.
Новые тесты: `tests/test_view_factory.py` (+5), `tests/test_theme.py` (+3).
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
- в __init__ собирает окно, шрифты и передаёт реестр вью из `ViewFactory`;
  мёртвый `_respawn_player()` удалён в Фазе 8.
`Entity` остаётся **God-классом геометрии** (9+ properties → `pygame.Rect`) — риск №1 не решён.

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
| 1. Модели зависят от `pygame.Rect` | ✅ Подтверждён (`Entity.rect`) |
| 2. Game как God-Object | ✅ **Снят** (декомпозирован) |
| 3. Enemy без физики/гравитации | ✅ Подтверждён (`apply_physics` только у Player) |
| 4. Физика пишет в rect напрямую | ✅ Подтверждён (осознанно) |

### i) Качество кода

- - ✅ Хардкод цветов монет/иконки вынесен в `config.colors` (Фаза 10);
  остаточный хардкод (при его наличии) — в `background.py`/`hud.py`.
- ✅ Типизация, docstrings, типизированные `try/except`.
- ✅ 297 тестов + CI-пайплайн.
- ⚠️ `Game.__init__` — масштабная фабричная композиция (много ответственности сборки).

---

## 2. Обновлённая оценка

**v1:** ≈ 6,5/10.
**v2:** ≈ 8,5/10.
**v3 (текущая):** ≈ **9,0/10**.

Обоснование: закрыты три фазы — удалён мёртвый код (Фаза 8), изолирована
OCP-регистрация вью в `ViewFactory` (Фаза 9), централизованы цвета монет
и иконки в `config.colors`/`coin_icon.py` (Фаза 10). 305 тестов.

До 9,5–10 не дотягивает из-за нерешённых рисков: `Entity`+`pygame.Rect`
(риск №1, Фаза 11), Enemy без физики (риск №3, Фаза 12), рассинхрон
README/JSON (Фаза 13).
---

## 3. Актуальные нарушения (с приоритетом)

**Критично:**
— (пусто) — все мины ImportError сняты в Фазе 8.

**Важно:**
- Риск №1 — `Entity` + `pygame.Rect` (крупный, отдельной фазой 11).
- Риск №3 — Enemy без физики/гравитации (Фаза 12).
- `Animatable` Protocol объявлен, но не используется (мелкий долг).

**Незначительно:**
- Рассинхрон README/JSON (персональные данные врагов) — Фаза 13.
- Массовая композиция в `Game.__init__` (уже ослаблена Фазами 7–9).
---

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

### Фаза 11 — Отделение геометрии от `pygame.Rect` (риск №1, крупный)
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

Фазы 8–10 закрыты. Дальше — **Фаза 11** (отделение геометрии от pygame.Rect):
крупный рефакторинг, требует полноценного набора тестов геометрии/коллизий
до начала изменений.

