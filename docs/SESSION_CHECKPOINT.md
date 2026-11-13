### Контекст проекта
- Игра JumpGame: пиксельный 2D-платформер, Python + pygame, MVC-архитектура.
- Структура: core/ (game, gameplay, level_flow, game_services, state_manager,
  level_transition, player_flow, game_over_handler), models/ (player, enemy,
  enemy_behavior, factory, collision_system, base_character, platform),
  views/ (renderer, render_state, sprite_cache, hud, tiles, background),
  controllers/, levels/, audio/, tests/.
### Выполненные фазы
- Phases 1-6: ядро, MVC, OCP-реестры поведений (walker/chaser/flyer/jumper),
  JSON-схема уровней (I1) + мигратор, каталог уровней по next_level (J2),
  переходы между уровнями и рестарт.
- Фаза 7 (рефакторинг декомпозиции Game + DIP, SRP) — ЗАВЕРШЕНА:
  1. [ГОТОВО] PlayerFlow (core/player_flow.py) — смерть/респавн/жизни.
  2. [ГОТОВО] LevelTransition (core/level_transition.py) — каталог/переходы.
  3. [ГОТОВО] GameOverHandler (core/game_over_handler.py) — фейд game-over и
     рестарт по R вынесены из Game; в Game остались прокси game_over/fade_*.
  4. [ГОТОВО] DIP: Game.__init__ принимает services (dict); main.py — Composition
     Root (окно/рендер/звук/ресурсы/фабрика). Итожен tests/test_game_dip.py.
  5. [ГОТОВО] Renderer.draw: fat-interface (~12 аргументов) -> RenderState DTO
     (views/render_state.py); Game._draw собирает RenderState и передаёт его.
- Все тесты зелёные: pytest tests/ -q -> 297 passed.

### Планы на следующий сеанс
- Фаза 7 закрыта. Возможные продолжения:
  * рефакторинг HUD/RetroBackground под RenderState-подход (ходы-дальше);
  * покрытие интеграционными/смоук-тестами запуска Game (level_1) без pygame;
  * выделение ещё более тонких сервисов (ScoreManager/LifeManager уже есть);
  * оптимизация SpriteCache/кэша платформ.

### Ключевые файлы на текущем этапе
- core/game.py — оркестратор; DI через services; прокси на game_over_handler;
  _draw собирает RenderState.
- main.py — Composition Root (собирает окно/рендер/звук/ресурсы/фабрику).
- core/game_over_handler.py — GameOverHandler (фейд + рестарт по R).
- views/renderer.py — Renderer; draw(state: RenderState).
- views/render_state.py — RenderState (DTO кадра).
- core/player_flow.py, core/level_transition.py, core/gameplay.py.
- tests/test_game_flow.py, test_player_flow.py, test_level_transition.py,
  test_game_over_handler.py, test_game_dip.py, test_renderer.py.

### Шаг 5 (выполнен) — детали
- Новый views/render_state.py: dataclass RenderState (entities, coins,
  coin_collected, flag_rect, score, lives, seconds, state_manager, won,
  game_over, fade_level, camera).
- views/renderer.py: draw(self, state: RenderState) — заменён fat-interface,
  тело переведено на state.* (поведение не менялось).
- core/game.py: _draw собирает RenderState(...) и вызывает renderer.draw(state).
- tests/test_renderer.py: фон/HUD/fade замоканы; проверены ветки базовый/won/
  game_over+пейджедФейд/монеты.

### Важно: ограничение агента
- python-агент НЕ запускается, если в контексте висит большой jumpgame.zip
  (превышение лимита ~262k токенов). Поэтому в таких сессиях:
  * задачи выполняются по кодам из предыдущих сообщений,
  * правки применяет пользователь вручную и прогоняет pytest.
- Коды изменённых файлов всегда выдаются для копирования, архивы НЕ грузятся.