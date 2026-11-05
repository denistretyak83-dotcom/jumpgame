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

        # Загружаем фон и тайлы
        self.background = RetroBackground()
        self.tiles = RetroTiles()

        # Кэш для спрайтов платформ, чтобы не рисовать их каждый кадр "на лету"
        self._platform_surfaces = {}
        self.current_platforms = []

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

    def draw(self, player, enemies, coins, coin_collected, flag_rect,
             score, lives, seconds, state_manager, won, game_over,
             fade_level, camera):
        screen = self.screen

        # 1. Очистка и фон
        # Заполняем фон цветом
        screen.fill(settings.colors['SKY'])
        # Рисуем параллакс (горы)
        self.background.draw(screen, camera.player_x)

        # 2. ПЛАТФОРМЫ (Исправление: рисуем их явно)
        if self.current_platforms:
            for p in self.current_platforms:
                # Получаем или создаём спрайт для этой платформы
                surf = self._platform_surface(p.width, p.height)
                screen.blit(surf, (p.x, p.y))

        # 3. МОНЕТЫ
        for i, coin in enumerate(coins):
            if not coin_collected[i]:
                # Рисуем монетку (ellipse)
                pygame.draw.ellipse(screen, (180, 130, 0), coin.inflate(2, 2))  # Тень/Обводка
                pygame.draw.ellipse(screen, (255, 220, 0), coin)  # Золотой круг
                pygame.draw.ellipse(screen, (255, 245, 120), coin.inflate(-8, -8))  # Блик

        # 4. ВРАГИ (Ваша логика отрисовки)
        if not player.is_dead:  # Можно рисовать врагов даже если игрок умер, но для простоты оставим так
            for enemy in enemies:
                if hasattr(enemy, 'current_anim') and enemy.current_anim:
                    frame = enemy.current_anim.current()
                    if frame is not None:
                        # Если враг смотрит влево, зеркалим спрайт
                        if hasattr(enemy, 'facing_left') and enemy.facing_left:
                            frame = pygame.transform.flip(frame, True, False)
                        screen.blit(frame, (enemy.rect.x, enemy.rect.y))

        # 5. ФЛАГ (Цель)
        if flag_rect:
            fx, fy = flag_rect.x, flag_rect.y
            # Древко
            pygame.draw.line(screen, settings.colors['BROWN'], (fx + 5, fy + 60),
                             (fx + 5, fy), 4)
            # Полотнище
            pygame.draw.polygon(screen, settings.colors['ORANGE'], [
                (fx + 5, fy), (fx + 30, fy + 12), (fx + 5, fy + 24)
            ])

        # 6. ИГРОК
        if not won:
            # Если игрок жив
            if not player.is_dead:
                frame = player.current_anim.current()
                if frame is not None:
                    y_offset = player.rect.bottom - frame.get_height()
                    x_offset = player.rect.x

                    if player.facing_left:
                        # Зеркалим прыжок и idle, если нужно (в зависимости от спрайтов)
                        if (player.current_anim is player.animations['idle'] or
                                player.current_anim is player.animations['jump']):
                            frame = pygame.transform.flip(frame, True, False)

                    screen.blit(frame, (x_offset, y_offset))
            else:
                # Анимация смерти (перевёрнутый idle)
                frame = player.animations['idle'].current()
                if frame is not None:
                    frame = pygame.transform.flip(frame, False, True)
                    screen.blit(frame, (player.rect.x, player.rect.y))

        # 7. ИНТЕРФЕЙС (HUD)
        draw_retro_hud(screen, self.small_font, self.small_font, score, lives,
                       seconds, self.coin_icon)

        # 8. СООБЩЕНИЯ (Победа / Поражение)
        if won:
            # Текст победы
            win_text = self.font.render("YOU WIN!", True, settings.colors['RED'])
            screen.blit(win_text, (settings.screen.width // 2 - 90,
                                   settings.screen.height // 2 - 40))
            restart = self.small_font.render("PRESS R TO RESTART", True,
                                             settings.colors['BLACK'])
            screen.blit(restart, (settings.screen.width // 2 - 110,
                                  settings.screen.height // 2))

        if game_over:
            # Затемнение экрана при проигрыше
            if fade_level < 180:
                go_text = self.font.render("GAME OVER!", True, settings.colors['RED'])
                screen.blit(go_text, (settings.screen.width // 2 - 100,
                                      settings.screen.height // 2 - 40))
                restart = self.small_font.render("PRESS R TO RESTART", True,
                                                 settings.colors['BLACK'])
                screen.blit(restart, (settings.screen.width // 2 - 110,
                                      settings.screen.height // 2))

            # Эффект затухания
            draw_pixelated_fade(screen, fade_level, grid=4)