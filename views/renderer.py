"""Renderer -- draws everything for a frame from models + game state."""

import pygame

from views.backgrounds import RetroBackground
from views.hud import draw_pixelated_fade, draw_retro_hud
from views.render_state import RenderState
from views.tiles import RetroTiles, TileFactory


class Renderer:
    def __init__(
        self, screen, sprite_cache, coin_icon, font, small_font, config, view_registry=None
    ):
        self._autotilers = {}  # style -> AutoTiler
        self.screen = screen
        self.sprite_cache = sprite_cache
        self.coin_icon = coin_icon
        self.font = font
        self.small_font = small_font
        self.config = config

        self.background = RetroBackground(
            screen_width=self.config.screen.width,
            screen_height=self.config.screen.height,
            config=self.config,
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

    # --- Фаза 9: замена реестра целиком (готовый, из ViewFactory) ---
    def set_view_registry(self, registry):
        """Назначает готовый реестр «тип -> вью» (строится в ViewFactory)."""
        self._view_registry = registry or {}

    # --- хелперы платформ ---
    def _platform_surface(self, width, height, style="grass_top", mask=0):
        key = (width, height, style, mask)
        if key not in self._platform_surfaces:
            surf = self._make_tile(style, width, height)
            self._draw_edges(surf, mask, width, height)
            self._platform_surfaces[key] = surf
        return self._platform_surfaces[key]

    @staticmethod
    def _make_tile(style, width, height):
        """OCP: выбирает генератор плитки по стилю (views.tiles)."""
        if style == "floating":
            return RetroTiles.floating_platform(width, height)
        if style == "brick":
            return TileFactory.brick_tile(width, height)
        if style == "grass_top_tile":
            return TileFactory.grass_top_tile(width, height)
        # default style ("grass_top") + fallback
        return RetroTiles.grass_top(width, height)

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
    def draw(self, state: RenderState):
        screen = self.screen

        # 1. Очистка и фон
        screen.fill(self.config.colors["SKY"])
        self.background.draw(screen, state.camera.player_x)

        # 2. PLATFORMS (автотайлинг: рёбра обводятся там, где нет соседа)
        if self.current_platforms:
            for p in self.current_platforms:
                style = getattr(p, "tile_style", "grass_top")
                mask = self._neighbor_mask(p)
                surf = self._platform_surface(p.width, p.height, style, mask)
                screen.blit(surf, (p.x, p.y))

        # 3. МОНЕТЫ
        for i, coin in enumerate(state.coins):
            if not state.coin_collected[i]:
                coin_rect = coin.to_pygame_rect()
                pygame.draw.ellipse(
                    screen, self._color("COIN_EDGE", (180, 130, 0)), coin_rect.inflate(2, 2)
                )
                pygame.draw.ellipse(screen, self._color("COIN", (255, 220, 0)), coin_rect)
                pygame.draw.ellipse(
                    screen, self._color("COIN_HILIGHT", (255, 245, 120)), coin_rect.inflate(-8, -8)
                )

        # 4. СУЩНОСТИ (игрок + враги)
        if not state.won:
            self.draw_entities(state.entities)

        # 5. ФЛАГ (Цель)
        if state.flag_rect:
            fx, fy = state.flag_rect.x, state.flag_rect.y
            pygame.draw.line(
                screen, self.config.colors["BROWN"], (fx + 5, fy + 60), (fx + 5, fy), 4
            )
            pygame.draw.polygon(
                screen,
                self.config.colors["ORANGE"],
                [(fx + 5, fy), (fx + 30, fy + 12), (fx + 5, fy + 24)],
            )

        # 6. ИНТЕРФЕЙС (HUD)
        draw_retro_hud(
            screen,
            self.small_font,
            self.small_font,
            state.score,
            state.lives,
            state.seconds,
            self.coin_icon,
            self.config,
        )

        # 7. СООБЩЕНИЯ
        if state.won:
            win_text = self.font.render("YOU WIN!", True, self.config.colors["RED"])
            screen.blit(
                win_text, (self.config.screen.width // 2 - 90, self.config.screen.height // 2 - 40)
            )
            restart = self.small_font.render(
                "PRESS R TO RESTART", True, self.config.colors["BLACK"]
            )
            screen.blit(
                restart, (self.config.screen.width // 2 - 110, self.config.screen.height // 2)
            )

        if state.game_over:
            if state.fade_level < 180:
                go_text = self.font.render("GAME OVER!", True, self.config.colors["RED"])
                screen.blit(
                    go_text,
                    (self.config.screen.width // 2 - 100, self.config.screen.height // 2 - 40),
                )
                restart = self.small_font.render(
                    "PRESS R TO RESTART", True, self.config.colors["BLACK"]
                )
                screen.blit(
                    restart, (self.config.screen.width // 2 - 110, self.config.screen.height // 2)
                )
            draw_pixelated_fade(screen, state.fade_level, self.config, grid=4)

    # --- Фаза 10: безопасное чтение цвета из конфига с fallback на дефолт ---
    def _color(self, key, default):
        """Возвращает цвет из config.colors, иначе -- default.

        Позволяет тестам не зависеть от всех ключей и не ломать рендер
        при отсутствии цвета в settings.json.
        """
        return self.config.colors.get(key, default)

    def _neighbor_mask(self, p) -> int:
        """Вычисляет маску соседей для платформы p по другим платформам.

        Бит TILE_MASK_TOP/BOTTOM/LEFT/RIGHT ставится, если с этой стороны
        есть соприкасающаяся платформа-сосед.
        """
        from views.tiles.autotile import (
            TILE_MASK_BOTTOM,
            TILE_MASK_LEFT,
            TILE_MASK_RIGHT,
            TILE_MASK_TOP,
        )

        mask = 0
        for other in self.current_platforms:
            if other is p:
                continue
            # gorizontal: одинаковый x-диапазон, соприкасается по y
            if other.x < p.x + p.width and other.x + other.width > p.x:
                # сосед снизу: верх other == низ p
                if abs(other.y - (p.y + p.height)) <= 2:
                    mask |= TILE_MASK_BOTTOM
                # сосед сверху: низ other == верх p
                if abs((other.y + other.height) - p.y) <= 2:
                    mask |= TILE_MASK_TOP
            # вертикаль: одинаковый y-диапазон, соприкасается по x
            if other.y < p.y + p.height and other.y + other.height > p.y:
                if abs(other.x - (p.x + p.width)) <= 2:
                    mask |= TILE_MASK_RIGHT
                if abs((other.x + other.width) - p.x) <= 2:
                    mask |= TILE_MASK_LEFT
        return mask

    def _draw_edges(self, surf, mask, width, height):
        """Обводит тёмной линией грани платформы, где НЕТ соседа (ФР-3.5)."""
        edge = (0, 0, 0)
        if not (mask & 1):  # top
            pygame.draw.rect(surf, edge, (0, 0, width, 2))
        if not (mask & 2):  # bottom
            pygame.draw.rect(surf, edge, (0, height - 2, width, 2))
        if not (mask & 4):  # left
            pygame.draw.rect(surf, edge, (0, 0, 2, height))
        if not (mask & 8):  # right
            pygame.draw.rect(surf, edge, (width - 2, 0, 2, height))
