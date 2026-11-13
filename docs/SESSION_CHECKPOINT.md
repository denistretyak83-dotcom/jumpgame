### Контекст проекта
- Игра JumpGame: пиксельный 2D-платформер, Python + pygame, MVC-архитектура.
- Структура: core/ (game, gameplay, level_flow, game_services, state_manager,
  level_transition, player_flow, game_over_handler), models/ (player, enemy,
  enemy_behavior, factory, collision_system, base_character, platform),
  views/ (renderer, sprite_cache), controllers/, levels/, audio/, tests/.
### Выполненные фазы
- Phases 1-6: ядро, MVC, OCP-реестры поведений (walker/chaser/flyer/jumper),
  JSON-схема уровней (I1) + мигратор, каталог уровней по next_level (J2),
  переходы между уровнями и рестарт.
- Фаза 7 (рефакторинг декомпозиции Game, SRP):
  1. [ГОТОВО] PlayerFlow (core/player_flow.py) — смерть/респавн/жизни вынесены.
  2. [ГОТОВО] LevelTransition (core/level_transition.py) — каталог уровней,
     next_level-переходы, рестарт вынесены.
  3. [ГОТОВО] GameOverHandler (core/game_over_handler.py) — вынесены из Game:
     ветка GAME_OVER в _update (фейд через _update_fade и рестарт по R через
     колбэк reset_run_state). В Game остались прокси-свойства
     game_over/fade_level/fade_direction, делегирующие в сервис. Добавлены
     тесты tests/test_game_over_handler.py; обновлены tests/test_game_flow.py
     под новый интерфейс.
- Все тесты зелёные: pytest tests/ -q -> 288 passed.

### Следующий шаг (завтра)
- Шаг 4 (DIP-декомпозиция Game): внедрять сервисы (PlayerFlow, LevelTransition,
  GameOverHandler, level_flow, collision_director и др.) через конструктор Game
  вместо создания внутри __init__ — с дефолтами, сохраняющими текущее поведение.
  Цель: Game зависел от абстракций; в тестах можно будет не использовать
  object.__new__(Game)-helперы, а подставлять моки через конструктор.
- После шага 4 — рефакторинг Renderer.draw (fat-interface, ~12 аргументов
  -> data-class).

### Ключевые файлы на текущем этапе
- core/game.py — оркестратор; создаёт сервисы внутри __init__ (SRP на уровне
  методов уже выполнен; DIP-инъекция — намечена в шаг 4). Содержит прокси
  game_over/fade_level/fade_direction на game_over_handler.
- core/player_flow.py — сервис смерти/респавна (готов).
- core/level_transition.py — сервис каталога/переходов (готов).
- core/game_over_handler.py — сервис экрана Game Over: фейд и рестарт по R
  (готов, шаг 3).
- core/gameplay.py — CollisionDirector (коллизии).
- views/renderer.py — рендер, кандидат на рефакторинг.
- tests/test_game_flow.py, tests/test_player_flow.py,
  tests/test_level_transition.py, tests/test_game_over_handler.py.

### Шаг 3 (выполнен) — детали реализации
- Новый core/game_over_handler.py: GameOverHandler(config, event_bus, reset_run_state).
  Методы: start() (флаг game_over + событие GAME_OVER + fade_direction=1),
  update(dt, keys) -> bool (True при рестарте по R), _update_fade(dt) (кламп в 255),
  reset().
- game.py: из _update удалена ветка GAME_OVER -> вызов game_over_handler.update(dt, keys);
  блок установки game-over при нехватке жизней -> game_over_handler.start();
  _update_game_over_fade удалён (логика в _update_fade); прокси-свойства
  game_over/fade_level/fade_direction на сервис (создаётся до reset_run_state()).
- Замечание: старые тесты на Game._update_game_over_fade мигрированы на GameOverHandler;
  в object.__new__(Game)-helперах добавлена привязка game_over_handler (фикстура).

### Важно: ограничение агента
- python-агент НЕ запускается, если в контексте висит большой jumpgame.zip
  (превышение лимита ~262k токенов). Поэтому в таких сессиях:
  * задачи выполняются по кодам из предыдущих сообщений,
  * правки применяет пользователь вручную и прогоняет pytest.
- Коды изменённых файлов всегда выдаются для копирования, архивы НЕ грузятся.