"""Renderer -- draws everything for a frame from models + game state."""
import pygame

from views.background import RetroBackground
from views.tiles import RetroTiles
from views.hud import draw_retro_hud, draw_pixelated_fade


class Renderer:
    def __init__(self, screen, sprite_cache, coin_icon, font, small_font, config,
                 view_registry=None):
        self.screen = screen
        self.sprite_cache = sprite_cache
        self.coin_icon = coin_icon
        self.font = font
        self.small_font = small_font
        self.config = config

        self.background = RetroBackground(
            screen_width=self.config.screen.width,
            screen_height=self.config.screen.height,
        )
        self.tiles = RetroTiles()

        self._platform_surfaces = {}
        self.current_platforms = []

        # Реестр: тип сущности -> фабрика вью (регистрируется извне)
        self._view_registry = view_registry or {}

    # --- новый метод: регистрация вью для типа сущности ---
    def register_view(self, entity_cls, view_factory):
        """OCP: новый тип сущности = регистрация, без правки Renderer."""
        self._view_registry[entity_cls] = view_factory

    # --- хелперы платформ ---
    def _platform_surface(self, width, height):
        key = (width, height)
        if key not in self._platform_surfaces:
            self._platform_surfaces[key] = self.tiles.grass_top(width, height)
        return self._platform_surfaces[key]

    def set_platforms(self, platforms):
        self.current_platforms = platforms

    @property
    def platforms(self):
        return self.current_platforms

    # ==================================================================
    # НОВЫЙ МЕТОД: единообразная отрисовка сущностей (ПОЛИМОРФИЗМ)
    # View получает ЛОГИЧЕСКОЕ состояние от модели и превращает его в кадр.
    # ==================================================================
    def _view_for(self, entity, data=None):
        if data is None:
            data = entity.get_visual_data()
        # Если есть anim_group (враг) — вью по sprite-ключу
        if data.anim_group is not None:
            return self.sprite_cache.enemy_view(data.anim_group)
        # Иначе — по классу из реестра (Player)
        for entity_cls, view_factory in self._view_registry.items():
            if isinstance(entity, entity_cls):
                return view_factory()
        return None

    def draw_entities(self, entities):
        for entity in entities:
            data = entity.get_visual_data()
            view = self._view_for(entity, data)  # передаём data
            if view is None:
                continue
            state = view.build_state(data)  # View строит DTO
            frame, x, y = view.render(state)
            if frame is None:
                continue
            self.screen.blit(frame, (x, y))

    # ==================================================================
    def draw(self, entities, coins, coin_collected, flag_rect,
             score, lives, seconds, state_manager, won, game_over,
             fade_level, camera):
        screen = self.screen

        # 1. Очистка и фон
        screen.fill(self.config.colors['SKY'])
        self.background.draw(screen, camera.player_x)

        # 2. ПЛАТФОРМЫ
        if self.current_platforms:
            for p in self.current_platforms:
                surf = self._platform_surface(p.width, p.height)
                screen.blit(surf, (p.x, p.y))

        # 3. МОНЕТЫ
        for i, coin in enumerate(coins):
            if not coin_collected[i]:
                pygame.draw.ellipse(screen, (180, 130, 0), coin.inflate(2, 2))
                pygame.draw.ellipse(screen, (255, 220, 0), coin)
                pygame.draw.ellipse(screen, (255, 245, 120), coin.inflate(-8, -8))

        # 4. СУЩНОСТИ (игрок + враги)
        if not won:
            self.draw_entities(entities)

        # 5. ФЛАГ (Цель)
        if flag_rect:
            fx, fy = flag_rect.x, flag_rect.y
            pygame.draw.line(screen, self.config.colors['BROWN'], (fx + 5, fy + 60),
                             (fx + 5, fy), 4)
            pygame.draw.polygon(screen, self.config.colors['ORANGE'], [
                (fx + 5, fy), (fx + 30, fy + 12), (fx + 5, fy + 24)
            ])

        # 6. ИНТЕРФЕЙС (HUD)
        draw_retro_hud(screen, self.small_font, self.small_font, score, lives,
                       seconds, self.coin_icon, self.config)

        # 7. СООБЩЕНИЯ
        if won:
            win_text = self.font.render("YOU WIN!", True, self.config.colors['RED'])
            screen.blit(win_text, (self.config.screen.width // 2 - 90,
                                   self.config.screen.height // 2 - 40))
            restart = self.small_font.render("PRESS R TO RESTART", True,
                                             self.config.colors['BLACK'])
            screen.blit(restart, (self.config.screen.width // 2 - 110,
                                  self.config.screen.height // 2))

        if game_over:
            if fade_level < 180:
                go_text = self.font.render("GAME OVER!", True, self.config.colors['RED'])
                screen.blit(go_text, (self.config.screen.width // 2 - 100,
                                      self.config.screen.height // 2 - 40))
                restart = self.small_font.render("PRESS R TO RESTART", True,
                                                 self.config.colors['BLACK'])
                screen.blit(restart, (self.config.screen.width // 2 - 110,
                                      self.config.screen.height // 2))
            draw_pixelated_fade(screen, fade_level, self.config, grid=4)