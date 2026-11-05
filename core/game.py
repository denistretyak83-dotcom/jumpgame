"""Game -- Orchestrator: main loop, state, and MVC wiring."""
import pathlib
import pygame
from core.config import settings
from core.event_bus import EventBus
from core.state_manager import StateManager, GameState
from core.camera import ParallaxCamera
from core.asset_loader import AssetLoader
from views.animation import Animation
from views.renderer import Renderer
from views.player_view import PlayerView
from models.factory import WorldFactory
from models.player import Player
from levels.level_manager import LevelManager
from audio.sound_manager import SoundManager
from controllers.player_controller import PlayerController
from controllers.enemy_controller import EnemyController  # <--- Добавлено
from models.collision import (
    check_coin_collision, check_enemy_collision,
    check_flag_collision, check_fell_out
)


class Game:
    def __init__(self, root_dir=None):
        if root_dir is None:
            root_dir = str(pathlib.Path(__file__).resolve().parent.parent)
        self.root = pathlib.Path(root_dir)
        self.config = settings

        # --- Core Systems ---
        self.event_bus = EventBus()
        self.state = StateManager()
        self.camera = ParallaxCamera()

        # --- Assets & Audio ---
        self.assets = AssetLoader(str(self.root))
        self.sounds = SoundManager(self.assets.sounds_abs)

        # --- Screen & Renderer ---
        self.screen = pygame.display.set_mode((settings.screen.width, settings.screen.height))
        pygame.display.set_caption(settings.screen.caption)
        self.clock = pygame.time.Clock()

        self.font = self.assets.get_font(settings.assets.font_size)
        self.small_font = self.assets.get_font(settings.assets.small_font_size)
        self.coin_icon = self._make_coin_icon()
        self.renderer = Renderer(self.screen, self.assets, self.coin_icon,
                                 self.font, self.small_font, self.config)

        # --- Controllers ---
        self.player_controller = PlayerController()
        self.enemy_controller = EnemyController()  # <--- Добавлено

        # --- Factories & Animations ---
        self.world_factory = WorldFactory(self.assets, self.config)
        self.player_anims = self._build_player_animations()
        self.enemy_anims = self._build_enemy_animations()

        # --- Level Management ---
        self.level_manager = LevelManager(self.root, entity_factories={
            "enemy": lambda d: self.world_factory.create_enemy(d, self.enemy_anims),
            "platform": lambda d: pygame.Rect(d["x"], d["y"], d["w"], d["h"]),
            "flag": lambda d: pygame.Rect(d["x"], d["y"], d["w"], d["h"]),
            "coin": lambda d: pygame.Rect(d["x"], d["y"], d["w"], d["h"]),
        })

        # --- Game State Vars ---
        self.lives = settings.game.lives
        self.score = 0
        self.frame_count = 0
        self.fade_level = 0
        self.fade_direction = 0
        self.won = False
        self.game_over = False

        # Event Listeners
        self.event_bus.subscribe("score_changed", lambda s: setattr(self, "score", s))
        self.event_bus.subscribe("lives_changed", lambda l: setattr(self, "lives", l))

        # Initialize
        self.reset_run_state()

    # --- Helpers ---
    def _make_coin_icon(self):
        icon = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(icon, (255, 200, 0), (8, 8), 7)
        pygame.draw.circle(icon, (255, 240, 100), (6, 6), 4)
        return icon

    def _build_player_animations(self):
        pf = self.world_factory.load_player_frames()
        return {
            "idle": Animation(pf["idle"], 10),
            "run_l": Animation(pf["run_l"], 6),
            "run_r": Animation(pf["run_r"], 6),
            "jump": Animation(pf["jump"], 8, loop=False),
        }

    def _build_enemy_animations(self):
        ef = self.world_factory.load_enemy_frames()
        return {"walk": Animation(ef["walk"], 8)}

    # --- Main Loop ---
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(settings.screen.fps) / 1000.0
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

    def _update(self, dt):
        # Получаем все нажатые клавиши один раз за кадр
        keys = pygame.key.get_pressed()

        # 1. Обработка состояний конца игры + РЕСТАРТ
        if self.state.has_ended():
            if keys[pygame.K_r]:
                # Рестарт по нажатию R
                self.reset_run_state()
                return

            if self.game_over:
                self._update_game_over_fade(dt)
            return

        if not self.state.is_playing():
            return

        # 2. Обработка смерти игрока
        if self.player.is_dead:
            if self.player.update_death(dt):
                self.lives -= 1
                self.event_bus.emit("lives_changed", self.lives)
                if self.lives <= 0:
                    self.game_over = True
                    self.fade_direction = 1
                    self.state.set(GameState.GAME_OVER)
                else:
                    self._respawn_player()
            return

        # 3. Основной игровой цикл
        # Ввод
        self.player_controller.handle_input(self.player, keys, dt)
        # Физика и анимация
        self.player.update(dt, keys, self.level.platforms)

        # Логика игры
        self._handle_coin_collection()
        self.enemy_controller.update_all(self.enemies, dt)
        self._handle_enemy_collision()
        self._handle_flag_collision()
        self._handle_fall_out(dt)

        # Камера и счётчик
        self.camera.update(self.player.rect.x)
        self.frame_count += 1

    # --- Logic Modules ---
    def _handle_coin_collection(self):
        hit_indices = check_coin_collision(self.coins, self.coin_collected, self.player.rect)
        for idx in hit_indices:
            if not self.coin_collected[idx]:
                self.coin_collected[idx] = True
                new_score = self.score + 1
                self.event_bus.emit("score_changed", new_score)
                self.sounds.play_coin()

    def _handle_enemy_collision(self):
        if check_enemy_collision(self.player.rect, self.enemies) is not None:
            self.player.die()

    def _handle_flag_collision(self):
        if check_flag_collision(self.player.rect, self.level.flag_rect):
            self.won = True
            self.state.set(GameState.WON)
            self.sounds.play_win()

    def _handle_fall_out(self, dt):
        if check_fell_out(self.player.rect, settings.screen.height):
            self.player.die()

    def _update_game_over_fade(self, dt):
        if self.fade_direction == 1:
            self.fade_level += settings.game.fade_speed * dt
            if self.fade_level >= 255:
                self.fade_level = 255
                self.fade_direction = 0

    # --- Drawing ---
    def _draw(self):
        self.renderer.draw(
            self.player, self.enemies, self.coins, self.coin_collected,
            self.level.flag_rect, self.score, self.lives,
            self.frame_count, self.state, self.won, self.game_over,
            self.fade_level, self.camera
        )
        self.player_view.render(self.screen)

    # --- State Management ---
    def _respawn_player(self):
        """Возвращает игрока на точку спавна после потери жизни."""
        spawn_point = self.level.player_spawn
        self.player = self.world_factory.create_player(
            spawn_point[0], spawn_point[1],
            self.player_anims, self.sounds
        )
        self.player_view = PlayerView(self.player)
        self.camera.update(self.player.rect.x)

    def reset_run_state(self):
        """Полный перезапуск игры (кнопка R после победы/поражения)."""
        self.lives = settings.game.lives
        self.score = 0
        self.frame_count = 0
        self.fade_level = 0
        self.fade_direction = 0
        self.won = False
        self.game_over = False
        self.state.set(GameState.PLAYING)

        level_data = self.level_manager.load_level("level_1")
        self.level = level_data

        # === ВОТ ЭТОЙ СТРОЧКИ НЕ ХВАТАЛО ===
        self.renderer.set_platforms(level_data.platforms)
        # ===================================

        spawn_point = self.level.player_spawn

        self.player = self.world_factory.create_player(
            spawn_point[0], spawn_point[1],
            self.player_anims, self.sounds
        )
        self.player_view = PlayerView(self.player)

        self.coins = [r.copy() for r in level_data.coins]
        self.coin_collected = [False] * len(self.coins)
        self.enemies = [e.spawn_copy() for e in level_data.enemies]

        self.camera.update(self.player.rect.x)
        self.sounds.play_music()