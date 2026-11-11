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
from core.logger import GameLogger
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
        self.player_view = None  # (удалено — сущности рисует Renderer через get_render_info)

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
            if self.player.update_death(dt):
                if self.life_manager.lose_life():
                    self.game_over = True
                    self.event_bus.emit(GameEvents.GAME_OVER)
                    self.fade_direction = 1
                    self.state.set(GameState.GAME_OVER)
                else:
                    self._respawn_player()
            return

        # 3. Ввод через контроллер (keys НЕ попадает в Player)
        intent = self.controller.handle_input(keys)

        # Контекст кадра (больше не содержит keys)
        ctx = GameContext(
            platforms=self.level.platforms,
            screen_width=self.config.screen.width,
            player_x=self.player.rect.x if self.player else 0.0,
        )
        # 4. ПОЛИМОРФИЗМ: единый цикл обновления всех сущностей
        #    Player использует intent, Enemy его игнорирует.
        for entity in self.entities:
            entity.update(dt, ctx, intent)

        # 5. Логика игры: все коллизии за один проход (через CollisionDirector)
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
        # Сущности (player + враги) рисует Renderer через get_render_info()
        self.renderer.draw(
            self.entities,  # <-- единый список вместо player/enemies
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
        # player_view рендер УДАЛЁН — отрисовка игрока внутри Renderer.draw_entities

    def _update_game_over_fade(self, dt):
        if self.fade_direction == 1:
            self.fade_level += self.config.game.fade_speed * dt
            if self.fade_level >= 255:
                self.fade_level = 255
                self.fade_direction = 0

    # --------------------------------------------------------------
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

        # Жизненный цикл уровня делегируется LevelFlow (Фаза 3)
        self.level_flow.load_and_setup("level_1")

        # Забираем построенный мир из LevelFlow
        self.level = self.level_flow.level
        self.player = self.level_flow.player
        self.entities = self.level_flow.entities
        self.coins = self.level_flow.coins
        self.coin_collected = self.level_flow.coin_collected
