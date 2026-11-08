"""Game -- Orchestrator: main loop, state, and MVC wiring."""
import pathlib
import pygame

from core.config import Settings
from core.event_bus import EventBus, GameEvents
from core.state_manager import StateManager, GameState
from core.camera import ParallaxCamera
from core.asset_loader import AssetLoader
from core.context import GameContext
from views.renderer import Renderer
from core.game_services import LifeManager, ScoreManager, RespawnService
from models.factory import WorldFactory
from levels.level_manager import LevelManager
from controllers.player_controller import PlayerController
from audio.audio_listener import attach_audio_listener
from audio.sound_manager import SoundManager
from models.collision_system import CollisionSystem
from core.logger import GameLogger
from views.sprite_cache import SpriteCache
from models.player import Player
from models.enemy import Enemy


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
            self.screen, self.sprite_cache, self.coin_icon,
            self.font, self.small_font, self.config,
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

        # 5. Логика игры: все коллизии за один проход
        self._apply_collisions(dt)

        # 6. Камера и счётчик
        self.camera.update(self.player.rect.x)
        self.frame_count += 1

    # --------------------------------------------------------------
    def _draw(self):
        # Сущности (player + враги) рисует Renderer через get_render_info()
        self.renderer.draw(
            self.entities,  # <-- единый список вместо player/enemies
            self.coins, self.coin_collected,
            self.level.flag_rect,
            self.score_manager.score,
            self.life_manager.lives,
            self.frame_count,
            self.state,
            self.won,
            self.game_over,
            self.fade_level,
            self.camera
        )
        # player_view рендер УДАЛЁН — отрисовка игрока внутри Renderer.draw_entities

    def _apply_collisions(self, dt):
        """Централизованная обработка всех коллизий за один проход (R6)."""
        c = self.collision_system.check(
            self.player.rect,
            self.coins, self.coin_collected,
            [e for e in self.entities if e is not self.player],
            self.level.flag_rect,
        )

        # --- монета ---
        if c.coin_index is not None:
            self.coin_collected[c.coin_index] = True
            self.score_manager.add_points(1)
            self.event_bus.emit(GameEvents.COIN_COLLECTED, self.score_manager.score)
            self.sounds.play_coin()

        # --- враг ---
        if c.hit_enemy is not None:
            self.event_bus.emit(GameEvents.PLAYER_DIED)
            self.player.die(launch_up=False)

        # --- флаг ---
        if c.hit_flag:
            self.event_bus.emit(GameEvents.LEVEL_WON)
            self.won = True
            self.state.set(GameState.WON)
            self.sounds.play_win()

        # --- падение ---
        if c.fell_out:
            self.event_bus.emit(GameEvents.PLAYER_DIED)
            self.player.die(launch_up=False)

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
        self.state.set(GameState.PLAYING)

        level_data = self.level_manager.load_level("level_1")
        self.level = level_data
        self.renderer.set_platforms(level_data.platforms)

        spawn_point = self.level.player_spawn

        # 1) Явно создаём игрока ДО построения списка
        self.player = self.world_factory.create_player(
            spawn_point[0], spawn_point[1], self.event_bus
        )

        # 2) Список сущностей: [реальный игрок] + враги
        self.entities = [self.player] + [e.spawn_copy() for e in level_data.enemies]

        self.coins = [r.copy() for r in level_data.coins]
        self.coin_collected = [False] * len(self.coins)

        self.camera.update(self.player.rect.x)
        self.sounds.play_music()
