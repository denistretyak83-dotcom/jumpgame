# Отчёт — Фаза 0 «Санитизация и безопасность»

**Проект:** «Jump & Reach the Flag» (2D-платформер, Python + Pygame)
**Архив:** `jumpgame.zip` (file_id `c43e88f8-59ba-4716-abb2-4643ee4f556d`)
**Вывод артефактов:** `jumpgame_clean.zip` (исправленный проект) + `SANITIZE_REPORT.md` (этот отчёт)

---

## 1. Цель фазы

Убрать мёртвый код и немедленные «мины» (в первую очередь — `controllers/enemy_controller.py`, который импортирует несуществующий глобальный `settings` и мог бы вызывать `ImportError`), **не меняя поведение игры** и не выходя за рамки санитизации (никакого рефакторинга Game/Physics тап. — это Фаза 3).

Принципы: консервативность — удалять **только** файлы, которые точно нигде не импортируются и не являются точкой входа; перед удалением — полная проверка графа импортов.

---

## 2. Метод проверки фактического состояния (не полагался только на контекст)

1. **Распаковка:** `zipfile` извлёк исходник в рабочую директорию.
2. **Сканирование пакетов:** перечислены все `.py`/`.json`/`.md` в проекте.
3. **Построение графа импортов:** для каждого `.py` распарсены `import X` / `from X import Y` (после снятия строковых комментариев), составлена карта «кто импортирует кого».
4. **Поиск динамических загрузок:** проверено отсутствие `importlib` / `__import__` / `exec(` / `eval(` (динамических ссылок на модули нет).
5. **Поиск строковых упоминаний кандидатов** во всех `.py`, `.md`, `.json`, чтобы отличить реальные импорты от упоминаний в комментариях/строк-метод.
6. **Проверка после правок:** `py_compile` всех `.py` + импорт модулей (с учётом недоступного в headless pygame).

---

## 3. Результаты анализа

### 3.1 Никто не импортирует — кандидаты на удаление

По графу импортов следующие `.py` не импортируются ни одним другим модулем проекта:

| Модуль | Вывод | Решение |
|---|---|---|
| `controllers/enemy_controller.py` | Не используется (только импортирует `core.config`, но никто не импортирует его). Содержит `from core.config import settings` — **мина** (глобального `settings` в `core/config.py` нет, только класс `Settings`). | **УДАЛЁН** |
| `views/player_view.py` | Не используется; читает `player.animations/current_anim` (таких атрибутов в моделях нет) — мёртвый MVC-нарушитель. `player_view` в `core/game.py`/`sprite_cache.py` — это **метод** `SpriteCache.player_view()`, а не модуль. | **УДАЛЁН** |
| `models/collision.py` | Не используется; дублирует `CollisionSystem` (R6), `check_fell_out` хардкодит буфер `30`. | **УДАЛЁН** |

### 3.2 Не удалять (обходить)

| Элемент | Причина |
|---|---|
| `*.py` в `__pycache__` | Компилированные артефакты (удаляются из чистой сборки, не относятся к исходникам). |
| все `__init__.py` пакетов | Структурные маркеры пакетов; `audio/__init__.py` и др. импортируются неявно при импорте подмодулей. **Сохранены.** |
| `main.py` | Точка входа (не импортируется, но запускается напрямую). **Сохранён.** |

### 3.3 Удалён неиспользуемый протокол `Animatable`

- `models/behaviors.py`: класс `Animatable(Protocol)` присутствовал, но **нигде** не использовался (поиск по всему коду — только определение + докстрока). Не являлся базовым классом и не указывался в аннотациях.
- Выполнено: удалён класс, поправлен модульный docstring (убран фрагмент про Animatable), **сохранены** классы `DeathBehavior`, `RespawnBehavior`, `FallDeathBehavior`, `CallableRespawnBehavior`.

⚠️ **Была внесена правка в процессе:** при удалении блока `Animatable` из `models/behaviors.py` потерялся импорт `from typing import Any, Callable, Optional` (он был внутри удаляемого блока). Это было замечено проверкой импорта (`NameError: 'Any' is not defined`) и **исправлено** — строка `from typing import Any, Callable, Optional` восстановлена. Это единственная правка, добавленная сверх списка; она необходима, иначе `models/behaviors.py` не импортировался бы.

---

## 4. Список выполненных правок

| Файл | Действие | Причина |
|---|---|---|
| `controllers/enemy_controller.py` | **Удалён** | Мёртвый модуль; мина `from core.config import settings` (несуществующий глобал) → риск `ImportError`; нарушение DI-конвенции «без глобалов». |
| `views/player_view.py` | **Удалён** | Мёртвый модуль; нарушение MVC («View читает модель напрямую», обращается к несуществующим атрибутам). |
| `models/collision.py` | **Удалён** | Мёртвый модуль; дублирует `CollisionSystem`; магическое число `30` вместо `settings.collision.fall_buffer`. |
| `models/behaviors.py` | **Исправлен** | Удалён неиспользуемый `Animatable(Protocol)`; восстановлен/сохранён импорт `typing`; остальные классы не тронуты. |

**Не удалялись / не редактировались (оставлены с обоснованием):**
- Все `__init__.py` (структура пакетов) — сохранены.
- `main.py` (точка входа) — сохранён.
- `core/game.py`, `models/entity.py`, `models/physics.py` и остальная логика — **вне рамок Фазы 0** (декомпозиция/Protocol/геометрия — Фаза 3/4, не сейчас).

---

## 5. Итоговое дерево пакетов (после правок)

```
main.py
requirements.txt
README.md
config/settings.json                        # theme.json не было и не создавалось (это не входит в Фазу 0)

audio/  __init__.py, sound_manager.py, audio_listener.py
controllers/  __init__.py, player_controller.py          # enemy_controller.py УДАЛЁН
core/   __init__.py, game.py, config.py, logger.py,
        event_bus.py, state_manager.py, camera.py,
        game_services.py, context.py, asset_loader.py
levels/ __init__.py, level_manager.py, level_1.json
models/ __init__.py, entity.py, base_character.py, player.py, enemy.py,
        player_state.py, enemy_behavior.py, physics.py, behaviors.py,
        collision_system.py, model_state.py, factory.py   # collision.py УДАЛЁН
views/  __init__.py, renderer.py, sprite_cache.py, character_view.py,
        hud.py, background.py, tiles.py, animation.py     # player_view.py УДАЛЁН
```

Всего файлов в `jumpgame_clean.zip`: **42** (без `__pycache__`, без 3 удалённых модулей).

---

## 6. Результаты проверок

### 6.1 Синтаксис (py_compile)

- **38 .py файлов скомпилированы успешно, ошибок: 0.**

### 6.2 Импорты модулей

| Категория | Кол-во | Комментарий |
|---|---|---|
| Импортятся успешно (чистый Python) | 14 | `core.event_bus`, `core.config`, `core.state_manager`, `core.game_services`, `core.context`, `core.camera`, `core.logger`, `models.model_state`, `models.behaviors`, `models.enemy_behavior`, `models.physics`, `models.player_state`, `views.animation`, `audio.audio_listener` |
| Зависят от pygame (headless недоступен) | 17 | падают только на `No module named 'pygame'` — **ожидаемо в среде без pygame**, не дефект кода (`audio.sound_manager`, `core.game`, `core.asset_loader`, `levels.level_manager`, `models.entity/base_character/player/enemy/factory/collision_system`, `views.*`, `controllers.player_controller`) |
| **Реальные ошибки импорта** | **0** | — |

### 6.3 Проверка отсутствия удалённых модулей

- Статический поиск: `enemy_controller` / `import collision` / `models.collision` — **0 ссылок-импортов** в коде.
- Упоминания `player_view` — только **метод** `SpriteCache.player_view()` и комментарии, а не модуль.
- Удалённые модули **не импортируемы** (`ModuleNotFoundError` при попытке импорта — ожидаемо).

### 6.4 Поведение не изменено

- Не тронута игровая логика: коллизии (`CollisionSystem` чистый, возвращает `CollisionResult`), Game-оркестрация, EventBus, состояния, data-driven враги — без изменений.
- Удалены только **мёртвые** файлы, не подключённые к рантайму; точка входа `main.py` сохранена.

---

## 7. Наблюдения (вне обязанности, не правлено — для справки)

1. **`core/__init__.py` содержит некорректный комментарий** — текст «# Audio layer: procedural sound effects + looping background music.» (похоже на копипасту из `audio/__init__.py`). Это косметический дефект документации, поведение не затрагивает. **Оставлено** для консервативности; можно поправить в любой мелкой чистке.
2. **`pygame` не установлен** в среде (headless) — полноценный запуск `main.py` и импорт pygame-зависимых модулей невозможен, это ожидаемое ограничение, отражено в разделе 6.2.
3. Повтор `check_fell_out` с магическим `30` был в удалённом `models/collision.py` — `CollisionSystem` использует `settings.collision.fall_buffer`, так что после удаления дубля буфер един и конфигурируем.

---

## 8. Что дальше (не входит в эту фазу)

- **Фаза 1** «Инфраструктура качества»: CI/CD (G1), линтеры/типизация (G2), покрытие ≥80% (G3), pytest.
- После тестового фундамента — **Фаза 3** (декомпозиция Game, `PhysicsComponent`→Protocol) и **Фаза 4** (отказ от pygame.Rect).
- Рекомендуется поправить `core/__init__.py` (комментарий) при первом ревью.

---

## 9. Итог

Фаза 0 завершена: **удалено 3 мёртвых/дублирующих модуля** (`controllers/enemy_controller.py`, `views/player_view.py`, `models/collision.py`), **удалён неиспользуемый `Animatable(Protocol)`** из `models/behaviors.py`, восстановлен необходимый импорт `typing`. Синтаксис всех файлов корректен, чистых модулей импортятся без ошибок, поведение игры не изменено. Исправленный проект заархивирован в `jumpgame_clean.zip`.
