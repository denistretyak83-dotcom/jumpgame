"""Renderer -- draws everything for a frame from models + game state."""
import pygame
from core.config import settings
from views.background import RetroBackground
from views.tiles import RetroTiles
from views.hud import draw_retro_hud, draw_pixelated_fade


class Renderer:
    def __init__(self, screen, assets, coin_icon, font, small_font, config):
        self.screen = screen
        self.assets = assets
        self.coin_icon = coin_icon
        self.font = font
        self.small_font = small_font
        self.config = config

        self.background = RetroBackground()
        self.tiles = RetroTiles()

        self._platform_surfaces = {}
        self.current_platforms = []

    # --- хелперы платформ (РАБОЧИЕ) ---
    def _platform_surface(self, width, height):
        """Кэширует заранее отрисованную платформу по её размерам."""
        key = (width, height)
        if key not in self._platform_surfaces:
            self._platform_surfaces[key] = self.tiles.grass_top(width, height)
        return self._platform_surfaces[key]

    def set_platforms(self, platforms):
        """Устанавливает список платформ текущего уровня."""
        self.current_platforms = platforms

    @property
    def platforms(self):
        """Получает текущие платформы."""
        return self.current_platforms

    # ==================================================================
    # НОВЫЙ МЕТОД: единообразная отрисовка всех сущностей (ПОЛИМОРФИЗМ)
    # ==================================================================
    def draw_entities(self, entities):
        """Рисует каждую сущность через get_render_info().
        Renderer НЕ знает тип сущности — только данные из info.
        """
        for entity in entities:
            info = entity.get_render_info()
            frame = info.get('frame')
            if frame is None:
                continue

            rect = info['rect']

            # Позиция: игрок бликается от низа (bottom), враги — от верха (top).
            # Используем то, что сущность сама отдаёт в info — добавим ключ 'y'.
            draw_y = info.get('y', rect.y)
            self.screen.blit(frame, (rect.x, draw_y))

    # ==================================================================
    def draw(self, entities, coins, coin_collected, flag_rect,
             score, lives, seconds, state_manager, won, game_over,
             fade_level, camera):
        screen = self.screen

        # 1. Очистка и фон
        screen.fill(settings.colors['SKY'])
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

        # 4. СУЩНОСТИ (игрок + враги) — ЗАМЕНА блоков 4 и 6
        #    Условие: рисуем сущности, если не победа (игрок скрывается при выигрыше)
        if not won:
            self.draw_entities(entities)

        # 5. ФЛАГ (Цель)
        if flag_rect:
            fx, fy = flag_rect.x, flag_rect.y
            pygame.draw.line(screen, settings.colors['BROWN'], (fx + 5, fy + 60),
                             (fx + 5, fy), 4)
            pygame.draw.polygon(screen, settings.colors['ORANGE'], [
                (fx + 5, fy), (fx + 30, fy + 12), (fx + 5, fy + 24)
            ])

        # 6. ИНТЕРФЕЙС (HUD)
        draw_retro_hud(screen, self.small_font, self.small_font, score, lives,
                       seconds, self.coin_icon)

        # 7. СООБЩЕНИЯ
        if won:
            win_text = self.font.render("YOU WIN!", True, settings.colors['RED'])
            screen.blit(win_text, (settings.screen.width // 2 - 90,
                                   settings.screen.height // 2 - 40))
            restart = self.small_font.render("PRESS R TO RESTART", True,
                                             settings.colors['BLACK'])
            screen.blit(restart, (settings.screen.width // 2 - 110,
                                  settings.screen.height // 2))

        if game_over:
            if fade_level < 180:
                go_text = self.font.render("GAME OVER!", True, settings.colors['RED'])
                screen.blit(go_text, (settings.screen.width // 2 - 100,
                                      settings.screen.height // 2 - 40))
                restart = self.small_font.render("PRESS R TO RESTART", True,
                                                 settings.colors['BLACK'])
                screen.blit(restart, (settings.screen.width // 2 - 110,
                                      settings.screen.height // 2))
            draw_pixelated_fade(screen, fade_level, grid=4)