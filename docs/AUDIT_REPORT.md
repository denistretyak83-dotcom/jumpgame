# Аудит исходного кода «Jump & Reach the Flag»

**Анализируемый артефакт:** `jumpgame.zip`
**Метод:** статический анализ фактического кода (выборочное чтение ключевых классов, поиск по содержимому). Никаких догадок — каждый вывод привязан к файлу/классу.
**Дата:** редакция по итогам ревью плана (v2.0)

---

## 1. Структура проекта (ШАГ 1)

### 1.1 Дерево пакетов и файлов

```
jumpgame/
├── main.py                          # тонкая точка входа (DI-связка)
├── requirements.txt                 # только pygame
├── README.md                        # схема JSON-уровней, запуск, дерево
├── config/
│   └── settings.json                # ГЛОБАЛЬНЫЙ конфиг (магич. числа вынесены)
├── audio/
│   ├── sound_manager.py             # процедурная генерация звуков + BGM
│   └── audio_listener.py            # подписка звуков на EventBus
├── controllers/
│   ├── player_controller.py         # ЕДИНСТВЕННЫЙ читатель клавиатуры -> PlayerIntent
│   └── enemy_controller.py          # ⚠️ ЛЕГАСИ/МЁРТВЫЙ — импортирует несуществующий global settings
├── core/
│   ├── game.py                      # Game — оркестратор/God-Object
│   ├── config.py                    # Settings + dataclass-секции (R5)
│   ├── logger.py                    # GameLogger с ротацией (не синглтон)
│   ├── event_bus.py                 # токенизированный EventBus + GameEvents
│   ├── state_manager.py             # GameState + StateManager
│   ├── camera.py                    # ParallaxCamera (DI размеров)
│   ├── game_services.py             # Life/Score/Respawn сервисы (SRP)
│   ├── context.py                   # GameContext (контекст кадра)
│   └── asset_loader.py              # шрифты/спрайты (DI config)
├── models/
│   ├── entity.py                    # Entity + 9 зарезервированных properties
│   ├── base_character.py            # BaseCharacter (Entity + ABC + физика-композиция)
│   ├── player.py                    # Player + PlayerStateMachine
│   ├── enemy.py                     # Enemy (bound_left/right, поведение, pos_x)
│   ├── player_state.py              # FSM: Idle/Run/Jump/Fall
│   ├── enemy_behavior.py            # EnemyBehavior ABC + Walker/Chaser/Flyer + Registry
│   ├── physics.py                   # PhysicsComponent (запись напрямую в rect*)
│   ├── behaviors.py                 # DeathBehavior/RespawnBehavior (ABC) + Animatable (Protocol)
│   ├── collision_system.py          # CollisionSystem + Collidable (Protocol) + CollisionResult
│   ├── collision.py                 # ⚠️ ФУНКЦИИ-ХЕЛПЕРЫ коллизий (дублирующие CollisionSystem)
│   ├── model_state.py               # ModelVisualData (DTO без pygame)
│   └── factory.py                   # WorldFactory (registry OCP)
├── views/
│   ├── renderer.py                  # Renderer + view_registry (OCP)
│   ├── sprite_cache.py              # SpriteCache (вью сущностей)
│   ├── character_view.py            # CharacterView (DTO -> кадр)
│   ├── player_view.py               # ⚠️ ЛЕГАСИ/МЁРТВЫЙ — читает player.animations напрямую
│   ├── hud.py / background.py / tiles.py / animation.py
└── levels/
    ├── level_manager.py             # LevelManager + LevelBuilder (валидация JSON)
    └── level_1.json                 # Data-Driven уровень (враги с behavior/sprite)
```

### 1.2 Наличие юнит-тестов и конфиг-файлов

| Артефакт | Наличие | Комментарий |
|---|---|---|
| Юнит-тесты (`tests/`) | ❌ **ОТСУТСТВУЮТ** | Нет ни одного теста. План (4.4) декларирует «обязательное покрытие перед рефакторингом» — в коде его нет. **Критично.** |
| `config/settings.json` | ✅ Есть | Все константы вынесены (R5) |
| `config/theme.json` | ❌ **ОТСУТСТВУЕТ** | Раздел D (Theme/Skin-система) — только будущая работа; цвета хардкодятся в views (см. ниже) |

### 1.3 Непредусмотренные / проблемные модули

- **`controllers/enemy_controller.py` — мёртвый/легаси.** Делает `from core.config import settings`, но в `core/config.py` НЕТ глобального `settings` (только класс `Settings`). Модуль не импортируется `Game.py` (проверено: в `core/game.py` импортируются `PlayerController`, `CollisionSystem`, но НЕ `EnemyController`). ⇒ При импорте кидал бы `ImportError`. Реальная AI врагов живёт в `models/enemy_behavior.py`.
- **`views/player_view.py` — мёртвый/легаси, нарушает MVC.** Читает `player.animations`, `player.current_anim`, `player.rect` напрямую — но у `Player` эти атрибуты ОТСУТСТВУЮТ (Player использует FSM + get_visual_data; проверено: `animations`/`current_anim` в моделях не определяются). Файл не подключён к Renderer (тот использует CharacterView через SpriteCache). == остаток «View читает модель напрямую», противоречит конвенции 2.3/5.
- **`models/collision.py` — дублирует CollisionSystem.** Содержит `check_coin_collision/check_enemy_collision/check_flag_collision/check_fell_out` — те же проверки, что и класс `CollisionSystem` (R6). Это тот самый «легаси от централизации», плюс `check_fell_out` захардкожил буфер падения = 30 (магическое число, хотя `settings.json` имеет `collision.fall_buffer: 30`). Дубликат.

---

## 2. Аудит по осям (ШАГ 2)

### a) Структура и слои

**Вердикт: соответствует, с оговорками.**

Реальные пакеты совпадают с заявленными (models/views/controllers/core/levels/audio/main.py). Точка входа тонкая (`main.py`), как заявлено. Однако два лишних (мёртвых) файла — `controllers/enemy_controller.py` и `views/player_view.py` — не предусмотрены планом и нарушают чистоту слоёв. `models/collision.py` — дублирующий слой. `levels/*` существует и делает ровно заявленное (загрузка/построение из JSON через LevelManager/LevelBuilder).

### b) SOLID

#### S (Single Responsibility)
- **Соответствует (хорошие примеры):** `LifeManager`, `ScoreManager`, `RespawnService` (SRP-сервисы); `PlayerStateMachine`; поведенческие компоненты (`WalkerBehavior/ChaserBehavior/FlyerBehavior`); `PhysicsComponent`.
- **Нарушение:** `core/game.py::Game` — **God-Object, подтверждено.** В `_update()` напрямую: смерть игрока, ввод, контекст, обновление сущностей, `_apply_collisions(dt)` (вся игровая логика коллизий: монеты/враг/флаг/падение), камера. `Game` знает и про жизни, и про счёт, и про коллизии, и про звук, и про рестарт. Это ровно тот «раздел 4.2» плана.
- **Нарушение (плановое):** `models/entity.py::Entity` — класс с **9+ зарезервированными properties** (x,y,width,height,left,top,right,bottom,centerx,centery), делегирующими во внутренний `pygame.Rect`. По сути «God-класс геометрии». Это задокументировано планом (4.5), но в коде есть.

#### O (Open/Closed)
- **Соответствует:** `models/factory.py::WorldFactory` реализован как registry: `register()` / `create()` / `entity_factories()` — всё на месте, `_register_defaults` регистрирует platform/coin/flag/enemy, а `create_coin`/`create_platform` **отсутствуют** (проверено — дублей-заглушек НЕТ). План 4.3 («убрать дубли create_coin/create_platform») в коде уже фактически выполнен.
- **Дополнительно (сверх плана):** реестр поведений `EnemyBehaviorRegistry` + `Renderer.view_registry` + `register_view()` — три OCP-точки. **в2/в3 плана реализованы в коде даже сверх заявленного.**
- **Небольшое нарушение:** `core/game.py` строит `view_registry` через **lambda-фабрики инлайн в конструкторе Renderer** — регистрация вью для Player/Enemy происходит в Game, а не в SpriteCache/почтиц. Это приемлемо, но размазывает OCP-регистрацию по Game.

#### L (Liskov)
- **Соответствует базово:** композиция вместо наследования (PhysicsComponent, поведения) снижает потребность в LSP. `DeathBehavior`/`RespawnBehavior`/`EnemyBehavior`/`PlayerState` — ABC, наследники соблюдают контракты (`enter/exit/handle` у состояний, `attach/update` у поведений).
- **Проверка подстановки:** `Enemy` и `Player` взаимозаменяемы в цикле `Game._update` (`entity.update(dt, ctx, intent)`) и в `Renderer.draw_entities` (`get_visual_data()`). Работает.
- **Потенциальное нарушение (скрытое):** `BaseCharacter` завязан на `PhysicsComponent(config)`, но `Enemy` никогда не вызывает `apply_physics` (проверено — вызывается только из `Player`). Значит, общее поведение из `BaseCharacter` для врага частично мёртвое (physics есть, но не используется). Формально не нарушение LSP, но «неиспользуемый контракт» — стоит задокументировать (это и есть задача 4.3 «протокол контракта PhysicsComponent»).

#### I (Interface Segregation)
- **Соответствует частично:** есть честные `Protocol`: `Animatable` (views/behaviors), `Collidable` (collision_system).
- **Нарушение/расхождение с планом:** документ (2.2 п.4) заявляет `AnimatableCollidable (Protocol)` — **такого имени в коде НЕТ** (есть раздельные `Animatable` и `Collidable`). К тому же `Animatable` объявлен, но **нигде не используется** (проверено) — мёртвый протокол. `PhysicsComponent` в плане должен стать Protocol (4.3) — пока это **конкретный класс**, а не протокол: контракт не зафиксирован типом.
- **Нет `PlayableCharacter`** (раздел 3.B) — ожидаемо, это будущая работа, не нарушение.

#### D (Dependency Inversion)
- **В целом соответствует:** `main.py` — единственная точка `Settings() -> GameLogger(config=logging) -> Game(config, logger)`. DI через конструкторы. Глобалов/синглтонов в основной ветке НЕТ (`GameLogger` — обычный класс, удалён `__new__/_instance` из singleton).
- **Нарушение (критичное):** `controllers/enemy_controller.py` делает `from core.config import settings` + `self.config = config or settings` — ссылка на глобальный `settings`, которого не существует. Модуль мёртв, но сам факт — прямое нарушение конвенции «никаких глобалов» (5) и DI.
- **Исключения безопасности не мешают: `AssetLoader.__init__` падает на `Settings()` fallback, `WorldFactory` на `Settings()` fallback** — это локальные DI-fallback (приемлемо, без глобалов).

### c) MVC

**Вердикт: соответствует ядру, но Game и мёртвые вью нарушают чистоту.**

- **Model → DTO: ок.** Богатая модель отдаёт чистые `ModelVisualData` (dataclass без pygame) через `get_visual_data()` у `Player`/`Enemy`. ✅
- **View читает через DTO: ок для рабочего пути.** `Renderer.draw_entities` → `get_visual_data()` → `_view_for` → `CharacterView.build_state(data)` → `render()`. Renderer НЕ читает модель напрямую. ✅
- **Controller единственный читатель ввода: ок.** `PlayerController` конвертирует `pygame keys -> PlayerIntent`; keys не попадают в Player. ✅
- **Коллизии: НЕ в CollisionSystem.** Хотя `CollisionSystem` корректно возвращает чистый `CollisionResult` без мутаций, **все игровые правила (score, lives, события, смерть, флаг) применяются в `Game._apply_collisions`**. Раздел 4.2 прямо это и хочет вынести в `CollisionDirector/GameplayService`. Подтверждено.
- **Game — оркестратор И God-Object одновременно.** Из `core/game.py`: Game создаёт всю композицию (DI-сборка — это ок), но также содержит `_apply_collisions`, менеджмент фейда, смерть/респаун, прямое манипулирование `coin_collected`, `won`, `game_over`, звуками. = God-Object, подтверждено.

### d) EventBus (Observer)

**Вердикт: полностью соответствует.**

`core/event_bus.py`:
- Токенизированная подписка: `subscribe()` возвращает `_token_counter` инкремент (гарантированная уникальность, не `id(callback)`), `unsubscribe(token)`. ✅
- Изоляция ошибок: `emit()` оборачивает каждый callback в `try/except Exception`, сбой одного не роняет остальных. ✅
- Все события — константы `GameEvents.*` (SCORE/LIVES/GAME_OVER/LEVEL_WON/COIN_COLLECTED/PLAYER_DIED/PLAYER_JUMP/PLAYER_BUMP/CHARACTER_DEATH). ✅
- `GameLogger.attach()` использует безопасные fallback-строки при импорте GameEvents (нормализация try/except из плана). ✅

### e) Data-Driven уровни

**Вердикт: реализовано, соответствует.**

- `levels/level_1.json` → `LevelManager.load_level` → `LevelBuilder.build` (валидация обязательных ключей `player_spawn/platforms/flag`). ✅
- Все объекты строятся через `WorldFactory.entity_factories()` (фабрики из реестра). ✅
- **Персональные данные врагов + fallback на config.enemy:** `Enemy.__init__` берёт `behavior`/`sprite` из `enemy_data`, размеры из `config.enemy.width/height` (fallback). В JSON враги имеют `behavior: walker/chaser/flyer` и `sprite`. ✅ (в1 плана выполнено).
- **ПРИМЕЧАНИЕ (расхождение с README/планом):** JSON использует ключ `behavior`, а README описывает врагов как `{x,y,left,right}` без `behavior`. Также в JSON нет персональных `width/height/speed` на врага (план в1 заявлял «персональные width/height/speed/type» — в данных их нет, только behavior/sprite; размеры берутся из config). Частичное расхождение декларации и данных.

### f) State machine игрока

**Вердикт: полностью соответствует.**

`models/player_state.py`: `PlayerState(ABC)` + `IdleState/RunState/JumpState/FallState` + `PlayerStateMachine` c `handle()/enter()/exit()` и проверкой типа при переходе. `Player.get_visual_data()` берёт `self.state_machine.get_anim_key(self)`. ✅ (Патч 8 плана).

### g) Критичная конвенция (зарезервированные properties)

**Вердикт: соблюдена. Нарушений не найдено.**

- `Entity` — единственный владелец 9+ properties, делегирующих во внутренний `pygame.Rect`. ✅
- `Enemy` использует `bound_left`/`bound_right` (не `left`/`right` как поля), плюс собственные `pos_x`/`pos_y` (float-источник) — не конфликтует со свойствами. ✅
- `Player` использует только `self.rect.*` — не вводит собственных зарезервированных полей. ✅
- Поиск по коду не выявил наследников, присваивающих `self.left/self.right/self.x/...` с другой семантикой.

### h) Риски-реалии (подтверждение/опровержение)

| Риск из плана | Статус | Подтверждение по коду |
|---|---|---|
| 1. Зависимость моделей от pygame.Rect | ✅ **Подтверждён** | `Entity.rect = pygame.Rect(...)` напрямую в моделях (entity.py); Player/Enemy/физика используют `rect`. |
| 2. Game как God-Object | ✅ **Подтверждён** | `Game._apply_collisions`, менеджмент счёта/жизней/фейда/смерти/респауна внутри Game (game.py). |
| 3. Enemy без физики/гравитации | ✅ **Подтверждён** | `apply_physics` вызывается только из `Player`; `Enemy.update` → `behavior.update` (без физики). летающий `FlyerBehavior` игнорирует гравитацию/платформы. |
| 4. Прямое обращение физики к rect в обход properties | ✅ **Подтверждён (и это осознано)** | `PhysicsComponent.apply` пишет напрямую в `entity.rect.x/y/bottom/top/right/left`, а не через properties. Пока работает, т.к. properties делегируют в тот же rect, но при отказе от pygame.Rect (4.1) сломается. |

### i) Качество кода

- **Хардкод/магические числа:** в основном вынесены (R5). Остатки: `Game._make_coin_icon` (размер 16x16, цвета), `Renderer` при отрисовке монеты/флага/справочника, `models/collision.py::check_fell_out` (буфер `30` вместо `settings.collision.fall_buffer`), `views/background.py` (цвета/позиции гор/облаков). Цвета в `views/background.py` и `hud.py` хардкодятся напрямую, а не из `settings.colors` — несоответствие идее «магия -> settings.json».
- **try/except:** нормирован, типизирован (FileNotFoundError, OSError, KeyError, ValueError, pygame.error, JSONDecodeError). Болланд-хваталок (`except:` голых) нет. Места с `except Exception` — только осознанные (изоляция EventBus). ✅
- **Типизация:** активная, есть `Protocol`, `@runtime_checkable`, аннотированные контракты. Часть кода (Player/Enemy/handle_input) — с аннотациями. ✅ (но без mypy/pyright в проекте — нет конфига).
- **docstrings:** присутствуют и информативны в большинстве модулей (entity, behaviors, event_bus, config, factory, physics, collision_system). В `collision.py`, `background.py` — краткие. В целом хорошо.
- **Тесты:** ❌ отсутствуют полностью.
- **CI/линтеры:** ❌ отсутствуют (нет .github/, ruff/black конфигов).

---

## 3. Итоговый отчёт (ШАГ 3)

### 3.1 Сводка по осям

| Ось | Оценка | Ключевой пример |
|---|---|---|
| a) Структура и слои | **Соответствует** (с мусором) | Пакеты совпадают; но `enemy_controller.py` + `player_view.py` + `collision.py` — мёртвые/дублирующие |
| b) SOLID — S | **Частично** | Хорошие SRP-сервисы; но `Game` — God-Object, `Entity` — God-класс геометрии |
| b) SOLID — O | **Соответствует** | `WorldFactory.register/create/entity_factories`, `EnemyBehaviorRegistry`, `Renderer.register_view`; дублей `create_coin/platform` НЕТ |
| b) SOLID — L | **Частично** | Композиция снижает риски; `Enemy` не использует общий `PhysicsComponent` |
| b) SOLID — I | **Частично** | `Collidable`/`Animatable` Protocol есть; но `AnimatableCollidable` (из плана) отсутствует, `Animatable` не используется, `PhysicsComponent` — не Protocol |
| b) SOLID — D | **Соответствует с исключением** | DI через main.py; но `enemy_controller.py` ссылается на несуществующий global `settings` |
| c) MVC | **Соответствует ядру** | Model→DTO→View; Controller — единственный читатель ввода; но коллизии/правила в Game, а не в CollisionSystem |
| d) EventBus | **Полностью соответствует** | Токены + изоляция + GameEvents.* |
| e) Data-Driven | **Соответствует** | JSON→LevelBuilder→фабрики; враги с behavior + fallback на config |
| f) State machine | **Полностью соответствует** | Idle/Run/Jump/Fall + PlayerStateMachine |
| g) Конвенция properties | **Соответствует** | bound_left/right, pos_x/pos_y; нарушений нет |
| h) Риски | **Все 4 подтверждены** | pygame.Rect, Game God-Object, Enemy без физики, прямой rect |
| i) Качество кода | **Хорошее, без тестов** | Магия вынесена; типизация/докстринги ок; тестов/CI/линтеров НЕТ |

### 3.2 Таблица «Заявлено в плане vs Фактически в коде»

| Решение (план) | Фактический код | Статус |
|---|---|---|
| DI полный, точка main.py, без глобалов/синглтонов | `main.py` собирает `Settings→GameLogger→Game`; `GameLogger` не синглтон; **но** `enemy_controller.py` ссылается на глобальный `settings` (мёртвый модуль) | ✅ основное / ⚠️ 1 нарушение |
| MVC с DTO, модель без pygame | `ModelVisualData` (чистый dataclass), `get_visual_data()` | ✅ |
| View через DTO | `Renderer→CharacterView.build_state(data)`; Renderer не читает модель | ✅ |
| EventBus токенизированный + GameEvents.* | полная реализация в `core/event_bus.py` | ✅ |
| WorldFactory registry (OCP), убрать create_coin/platform (4.3) | registry реализован; **дублей-заглушек уже нет** | ✅ (опережает план) |
| EnemyBehavior Protocol + Registry (в2) | `EnemyBehavior` ABC + `EnemyBehaviorRegistry` + Walker/Chaser/Flyer | ✅ (реализовано сверх плана) |
| Анимации/вью под тип врага (в3) | `SpriteCache.enemy_view(sprite_key)`, `Renderer._view_for` по anim_group | ✅ (реализовано сверх плана) |
| Enemy с физикой/гравитацией (в4) | Enemy НЕ использует physics (Flyer игнорирует физику) | ❌ (будущее) |
| PlayableCharacter Protocol, несколько героев (B) | отсутствуют | ❌ (будущее) |
| State machine игрока (Патч 8) | `PlayerStateMachine` + Idle/Run/Jump/Fall | ✅ |
| Data-Driven враги (в1) с width/height/speed/type | враги из JSON с `behavior`/`sprite`; **персональных width/height/speed в данных НЕТ** (fallback на config) | ⚠️ частично |
| Конвенция properties (bound_left/right) | соблюдена в Enemy, Player, Entity | ✅ |
| Юнит-тесты, обязательные перед рефакторингом (4.4) | ❌ **нет `tests/`** | ⚠️ критичный разрыв |
| HUD Theme/Skin-система (D) | нет `theme.json`, цвета хардкодятся | ❌ (будущее) |
| Отказ от pygame.Rect (4.1), отделение геометрии (4.5) | `Entity.rect = pygame.Rect`; геометрия не отделена | ❌ (будущее, риск №1 подтверждён) |
| Декомпозиция Game (4.2, 4.6) | `Game._apply_collisions` инлайн, правила в Game | ❌ (будущее, риск №2 подтверждён) |

### 3.3 Найденные нарушения/расхождения (с приоритетом)

**Критично:**
1. **`controllers/enemy_controller.py` ссылается на несуществующий global `settings`** (`from core.config import settings`) — нарушение D, конвенции «без глобалов» (5), и потенциальный `ImportError`. (Модуль мёртв, но код — мина.)
2. **Отсутствие юнит-тестов** — план декларирует покрытие как обязательное условие (4.4, конвенция «тестирование»), фактически ноль тестов. Блокирует безопасность рефакторингов (4.1/4.5/4.2).

**Важно:**
3. **`Game` — God-Object** — все игровые правила (коллизии/счёт/жизни/фейд/респаун) в одном классе; подтверждён риск №2. План 4.2/4.6 не выполнен.
4. **Мёртвый `views/player_view.py`** — читает модель напрямую (`player.animations/current_anim`, которых нет), нарушает MVC и конвенцию «View не читает модель» (2.3/5). Не подключён, но загрязняет слой.
5. **Дублирующий `models/collision.py`** — функции-хелперы дублируют `CollisionSystem`, `check_fell_out` хардкодит `30` (магия) вместо `settings.collision.fall_buffer`.
6. **`Animatable` Protocol объявлен, но не используется**; заявленный в плане `AnimatableCollidable` в коде отсутствует (фактически два разных протокола).
7. **Data-Driven враги неполные** — в JSON нет персональных width/height/speed/type врагов (план в1 заявлял их), только behavior/sprite; размеры из config.

**Незначительно:**
8. Хардкод цветов/размеров в `views/background.py`, `views/hud.py`, `models/collision.py` вместо `settings.colors`/`collision.fall_buffer`.
9. `Renderer` view_registry строится lambda-фабриками прямо в `Game.__init__` — OCP-регистрация размазана по God-Object.
10. `Enemy` не использует унаследованный `PhysicsComponent` — «мёртвый контракт» в `BaseCharacter`.

### 3.4 Оценка фактического соответствия «8/10»

**Инженерная оценка фактического кода: ≈ 6,5/10** (не «8/10» из плана).

Обоснование:
- **+ сильные стороны:** DI без глобалов (основной путь), MVC «модель→DTO→View», полноценный токенизированный EventBus с изоляцией, честный OCP-реестр WorldFactory, реализованная сверх плана EnemyBehavior-фреймворк (Walker/Chaser/Flyer + registry), state machine, актуальная типизация и docstrings.
- **− расхождения и мягков:** (1) ноль юнит-тестов при декларируемой обязательности; (2) Game-God-Object и коллизии не вынесены; (3) мёртвые/дублирующие модули (`enemy_controller`, `player_view`, `collision.py`) загрязняют слои; (4) неиспользуемый Protocol `Animatable` и отсутствие заявленного `AnimatableCollidable`; (5) частичная реализация Data-Driven врагов (нет персональных размеров в данных); (6) мина с глобальным `settings` в `enemy_controller`.

Итог: код качественный по основным архитектурным осям (DI/MVC-Observer/OCP), но **«8/10» справедливо только для задекларированных принципов, а не для фактической консистентности**: мусорные файлы, отсутствие тестов/CI и невынесенный Game тянут фактическую оценку ниже заявленной.

### 3.5 Рекомендации (с привязкой к плану)

1. **Удалить/решить судьбу мёртвых файлов.** Удалить `controllers/enemy_controller.py` (или починить `import` на `Settings` и подключить) и `views/player_view.py`; свести `models/collision.py` в `CollisionSystem` или удалить. → **Раздел 4.3** («устранение дублей»).
2. **Добавить юнит-тесты как фундамент** (геометрия Entity, CollisionSystem, PhysicsComponent._resolve_, Enemy.apply_position до того, как она появится). → **Раздел 4.4**, критично до 4.1/4.5.
3. **Вынести коллизии и правила из Game в CollisionDirector/GameplayService**, инициировать через события, а не direct-вызовы. → **Раздел 4.2 + 4.6.**
4. **Отделить геометрию от Entity** — выделить `RectPosition`/`Geometry` объект, `Entity` оставить сущностным. → **Раздел 4.5** (уменьшит God-класс Entity и ослабит риск №1).
5. **Провести отказ от pygame.Rect в моделях** — `to_pygame_rect()` по требованию; перед этим тесты геометрии/коллизий. → **Раздел 4.1** (риск №1).
6. **Зафиксировать PhysicsComponent как Protocol** и задокументировать, почему Enemy не потребляет физику (в4 против композиции BaseCharacter). → **Раздел 4.3** + размышление по 3.A.в4.
7. **Согласовать JSON-схему с README и планом:** добавить персональные width/height/speed врагов в JSON либо явно зафиксировать fallback-контракт. → **Раздел 3.I1** (стабилизация JSON-схемы), 3.E.
8. **Подключить CI + линтеры + coverage** (ruff/black/isort, mypy/pyright, pytest+coverage ≥80% на моделях) — закроет риски №8 и снизит риск №11. → **Раздел 3.G1/G2/G3.**
9. **Вынести цвета фона/HUD и буфер падения в settings** (или создать theme.json) — убрать хардкод в `background.py`/`hud.py`/`collision.py`. → **Раздел 3.D/J1** (Theme-система) и принцип R5 («магические числа -> settings.json»).
10. **Убрать lambda-реестр вью из Game** — инкапсулировать регистрацию в `SpriteCache`/фабрику вью, чтобы OCP-точки не жили в God-Object. → **Раздел 3.A.в3** и 4.2.

---

## Приложение: ключевые файлы и строки

- `main.py`: `settings=Settings(); logger=GameLogger(config=settings.logging); game=Game(config=settings, logger=logger)` — точка DI.
- `core/game.py`: `_apply_collisions(dt)`, `_update(dt)`, `reset_run_state()` — God-Object.
- `models/entity.py`: 9+ properties, `self.rect = pygame.Rect(...)`.
- `models/factory.py`: `register()/create()/entity_factories()`, нет `create_coin/`/`create_platform`.
- `models/enemy_behavior.py`: `EnemyBehavior(ABC)` + `Walker/Chaser/Flyer` + `EnemyBehaviorRegistry`.
- `models/collision_system.py`: `Collidable(Protocol)`, `CollisionResult`, чистая `check()`.
- `core/event_bus.py`: токены `_token_counter`, изоляция в `emit()`, `GameEvents`.
- `levels/level_1.json`: враги `{behavior: walker/chaser/flyer, sprite: ...}`.
- `controllers/enemy_controller.py`: `from core.config import settings` → нарушение D/глобалов.
- `views/player_view.py`: читает `player.animations/current_anim` → мёртвый MVC-нарушитель.
- `models/collision.py`: `check_fell_out` с магическим `30`.
- `models/behaviors.py`: `Animatable(Protocol)` (не используется).
