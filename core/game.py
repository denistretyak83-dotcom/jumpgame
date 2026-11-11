"""Game -- Orchestrator: main loop, state, and MVC wiring."""

import pathlib

import pygame

from audio.audio_listener import attach_audio_listener
from audio.sound_manager import SoundManager
from controllers.player_controller import PlayerController
from core.asset_loader import AssetLoader
from core.camera import ParallaxCamera
from core.config import Settings
from core.context import GameContext
from core.event_bus import EventBus, GameEvents
from core.game_services import LifeManager, RespawnService, ScoreManager
from core.gameplay import CollisionDirector
from core.level_flow import LevelFlow
from core.level_transition import LevelTransition
from core.logger import GameLogger
from core.player_flow import PlayerFlow
from core.state_manager import GameState, StateManager
from levels.level_manager import LevelManager
from models.collision_system import CollisionSystem
from models.enemy import Enemy
from models.factory import WorldFactory
from models.player import Player
from views.renderer import Renderer
from views.sprite_cache import SpriteCache


class Game:
    def __init__(self, config=None, logger=None, root_dir=None):
        if root_dir is None:
            root_dir = str(pathlib.Path(__file__).resolve().parent.parent)
        self.root = pathlib.Path(root_dir)
        self.config = config or Settings()

        # DI: логгер инжектируется; создаётся из settings.logging, если не передан (R3)
        self.logger = logger or GameLogger(config=self.config.logging)

        # --- Core Systems ---
        self.event_bus = EventBus()
        self.state = StateManager()
        self.camera = ParallaxCamera(
            screen_width=self.config.screen.width,
            screen_height=self.config.screen.height,
        )

        self.logger.attach(
            self.event_bus,
            extra={
                GameEvents.PLAYER_DIED: ("Player", "Player died"),
                GameEvents.LEVEL_WON: ("Game", "Level won"),
                GameEvents.COIN_COLLECTED: ("Game", "Coin collected, total -> {0}"),
                GameEvents.GAME_OVER: ("Game", "GAME OVER"),
            },
        )

        # --- Assets & Audio ---
        self.assets = AssetLoader(str(self.root), self.config)
        self.sounds = SoundManager(self.assets.sounds_abs)

        self.controller = PlayerController()
        attach_audio_listener(self.event_bus, self.sounds)

        # --- Screen & Renderer ---
        self.screen = pygame.display.set_mode((self.config.screen.width, self.config.screen.height))
        pygame.display.set_caption(self.config.screen.caption)
        self.clock = pygame.time.Clock()

        # ██ R6: единая система коллизий (все проверки за один проход)
        self.collision_system = CollisionSystem(
            screen_height=self.config.screen.height,
            fall_buffer=self.config.collision.fall_buffer,
        )

        self.font = self.assets.get_font(self.config.assets.font_size)
        self.small_font = self.assets.get_font(self.config.assets.small_font_size)
        self.coin_icon = self._make_coin_icon()

        # ██ НОВОЕ: SpriteCache (View-слой анимаций) вместо player_anims/enemy_anims
        self.sprite_cache = SpriteCache(self.assets, self.config)

        self.renderer = Renderer(
            self.screen,
            self.sprite_cache,
            self.coin_icon,
            self.font,
            self.small_font,
            self.config,
            view_registry={
                Player: lambda: self.sprite_cache.player_view(),
                Enemy: lambda: self.sprite_cache.enemy_view(),
            },
        )

        # --- Factories ---
        self.world_factory = WorldFactory(self.assets, self.config)
        self.respawn_service = RespawnService(self.world_factory)

        # --- Level Management ---
        self.level_manager = LevelManager(
            self.root,
            entity_factories=self.world_factory.entity_factories(),
        )

        # --- Level Flow (декомпозиция игры, Фаза 3) ---
        self.level_flow = LevelFlow(
            level_manager=self.level_manager,
            world_factory=self.world_factory,
            event_bus=self.event_bus,
            renderer=self.renderer,
            camera=self.camera,
            sounds=self.sounds,
        )
        # НОВОЕ: LevelTransition (SRP) — каталог уровней и переходы вынесены из Game.
        self.level_transition = LevelTransition(
            level_manager=self.level_manager,
            level_flow=self.level_flow,
        )
        self.life_manager = LifeManager(self.config.game.lives, self.event_bus)
        self.score_manager = ScoreManager(self.event_bus)

        # --- Game State Vars ---

        self.frame_count = 0
        self.fade_level = 0
        self.fade_direction = 0
        self.won = False
        self.game_over = False
        self.enemies = []

        # --- Полиморфизм: единый список сущностей ---
        self.entities = []  # все движущиеся сущности (player + enemies)
        self.player = None  # быстрая ссылка на игрока
        self.player_view = None
        # НОВОЕ: PlayerFlow (SRP) — смерть/респавн/жизни вынесены из Game.
        self.player_flow = PlayerFlow(
            world_factory=self.world_factory,
            life_manager=self.life_manager,
            event_bus=self.event_bus,
        )

        # Event Listeners
        self.life_manager = LifeManager(self.config.game.lives, self.event_bus)
        self.score_manager = ScoreManager(self.event_bus)
        # --- Gameplay: обработка коллизий (вынесено из Game, Фаза 3) ---
        self.collision_director = CollisionDirector(
            collision_system=self.collision_system,
            score_manager=self.score_manager,
            event_bus=self.event_bus,
            sounds=self.sounds,
            state=self.state,
        )
        # Initialize
        self.reset_run_state()

    @property
    def current_level_name(self):
        # источник правды — в LevelTransition; если его нет (ранняя инициализация),
        # возвращаем внутренний кэш
        if hasattr(self, "_level_transition_cache"):
            return self._level_transition_cache
        return self.level_transition.current_level_name

    @current_level_name.setter
    def current_level_name(self, value):
        # Если level_transition ещё не создан, кэшируем во временный атрибут.
        # Как только он появится в __init__, синхронизируем.
        if not hasattr(self, "level_transition"):
            self._level_transition_cache = value
            return
        self.level_transition.current_level_name = value
        self._level_transition_cache = value

    # --- Helpers ---
    def _make_coin_icon(self):
        icon = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(icon, (255, 200, 0), (8, 8), 7)
        pygame.draw.circle(icon, (255, 240, 100), (6, 6), 4)
        return icon

    # --- Main Loop ---
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(self.config.screen.fps) / 1000.0
            running = self._process_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    # --------------------------------------------------------------
    def _update(self, dt):
        keys = pygame.key.get_pressed()

        # 1. Состояния конца игры + рестарт
        if self.state.has_ended():
            if self.state.current is GameState.WON:
                # Победа (флаг достигнут): сначала пробуем перейти на следующий
                # уровень через next_level (J2). Если переход выполнен — играем дальше.
                if self._advance_to_next_level():
                    return
                # Следующего уровня нет (это последний уровень каталога):
                # здесь обрабатываем рестарт по R; иначе остаёмся на экране победы.
                if keys[pygame.K_r]:
                    self.reset_run_state()
                    return
                return
            # GAME_OVER: рестарт или фейд
            if keys[pygame.K_r]:
                self.reset_run_state()
                return
            if self.game_over:
                self._update_game_over_fade(dt)
            return

        if not self.state.is_playing():
            return

        # Продвигаем анимации View-слоя каждый кадр
        self.sprite_cache.update(dt)

        # 2. Смерть игрока
        if self.player.is_dead:
            # True -> жизни закончились -> game over; False -> респавн; None -> смерть длится
            death_result = self.player_flow.update_death(dt)
            if death_result is True:
                self.game_over = True
                self.event_bus.emit(GameEvents.GAME_OVER)
                self.fade_direction = 1
                self.state.set(GameState.GAME_OVER)
            elif death_result is False:
                # PlayerFlow уже создал нового игрока; подменяем ссылку в entities и камеру
                for i, e in enumerate(self.entities):
                    if e is self.player:
                        self.entities[i] = self.player_flow.player
                        break
                self.player = self.player_flow.player
                self.camera.update(self.player.rect.x)
            return

        # 3. Ввод через контроллер
        intent = self.controller.handle_input(keys)

        ctx = GameContext(
            platforms=self.level.platforms,
            screen_width=self.config.screen.width,
            player_x=self.player.rect.x if self.player else 0.0,
        )
        # 4. Единый цикл обновления всех сущностей
        for entity in self.entities:
            entity.update(dt, ctx, intent)

        # 5. Логика игры: все коллизии за один проход
        self.collision_director.process(
            self.player,
            self.coins,
            self.coin_collected,
            self.entities,
            self.level.flag_rect,
        )

        # 6. Камера и счётчик
        self.camera.update(self.player.rect.x)
        self.frame_count += 1

    # --------------------------------------------------------------
    def _draw(self):
        self.renderer.draw(
            self.entities,
            self.coins,
            self.coin_collected,
            self.level.flag_rect,
            self.score_manager.score,
            self.life_manager.lives,
            self.frame_count,
            self.state,
            self.collision_director.won,
            self.game_over,
            self.fade_level,
            self.camera,
        )

    def _update_game_over_fade(self, dt):
        if self.fade_direction == 1:
            self.fade_level += self.config.game.fade_speed * dt
            if self.fade_level >= 255:
                self.fade_level = 255
                self.fade_direction = 0

    # --------------------------------------------------------------
    def _load_level(self, level_name: str):
        """Делегирует загрузку уровня LevelTransition и раскладывает мир по полям.

        Побочный эффект: сбрасывает победные/игровые флаги.
        """
        world = self.level_transition.load_level(level_name)
        self.current_level_name = self.level_transition.current_level_name
        self.level = world["level"]
        self.player = world["player"]
        self.entities = world["entities"]
        self.coins = world["coins"]
        self.coin_collected = world["coin_collected"]

        # Привязка к PlayerFlow
        self.player_flow.bind_level(self.level)
        self.player_flow.bind_player(self.player)

        self.won = False
        self.game_over = False
        self.collision_director.won = False

    def _advance_to_next_level(self) -> bool:
        """Делегирует переход на следующий уровень LevelTransition.

        True — следующий уровень загружен (снова играем); False — следующего
        нет (последний уровень, остаёмся на экране победы).
        """
        world = self.level_transition.advance_to_next_level()
        if world is None:
            return False
        self._apply_world(world)
        self.state.set(GameState.PLAYING)
        return True

    def _apply_world(self, world: dict):
        """Раскладывает мир, возвращённый LevelTransition, по атрибутам Game."""
        self.current_level_name = self.level_transition.current_level_name
        self.level = world["level"]
        self.player = world["player"]
        self.entities = world["entities"]
        self.coins = world["coins"]
        self.coin_collected = world["coin_collected"]
        self.player_flow.bind_level(self.level)
        self.player_flow.bind_player(self.player)
        self.won = False
        self.game_over = False
        self.collision_director.won = False

    def _respawn_player(self):
        spawn_point = self.level.player_spawn
        new_player = self.world_factory.create_player(
            spawn_point[0], spawn_point[1], self.event_bus
        )
        # Заменяем мёртвого игрока на нового в списке сущностей
        for i, e in enumerate(self.entities):
            if e is self.player:
                self.entities[i] = new_player
                break
        self.player = new_player
        self.camera.update(self.player.rect.x)

    def reset_run_state(self):
        """Полный перезапуск игры (кнопка R после победы/поражения)."""
        self.life_manager.reset(self.config.game.lives)
        self.score_manager.reset()
        self.frame_count = 0
        self.fade_level = 0
        self.fade_direction = 0
        self.won = False
        self.game_over = False
        self.collision_director.won = False
        self.state.set(GameState.PLAYING)

        # Рестарт с первого уровня через LevelTransition.
        self._load_level("level_1")
