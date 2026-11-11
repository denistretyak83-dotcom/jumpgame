"""HUD -- retro 90s HUD panel + pixelated fade (ported from main.py).

DI (R3): функции получают конфиг (Settings) через параметры, а не читают
глобальный settings.
"""

import pygame


def draw_retro_hud(
    screen, font, small_font, coins, lives, time, coin_icon, config, instructions=True
):
    """90s-style HUD with boxes and icons."""
    panel = pygame.Surface((230, 65), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 120))
    screen.blit(panel, (10, 10))

    pygame.draw.rect(screen, (255, 255, 255), (10, 10, 230, 65), 2)
    pygame.draw.rect(screen, (170, 170, 255), (12, 12, 226, 61), 1)

    screen.blit(coin_icon, (22, 22))
    coin_text = font.render(f"x{coins}/{config.game.coins_total}", True, (255, 220, 0))
    screen.blit(coin_text, (48, 22))

    lives_text = font.render(f"LIVES x{lives}", True, (255, 80, 80))
    screen.blit(lives_text, (20, 42))

    time_panel = pygame.Surface((120, 35), pygame.SRCALPHA)
    time_panel.fill((0, 0, 0, 120))
    screen.blit(time_panel, (config.screen.width - 130, 10))
    pygame.draw.rect(screen, (255, 255, 255), (config.screen.width - 130, 10, 120, 35), 2)
    time_text = font.render(f"TIME {time}", True, (255, 255, 255))
    screen.blit(time_text, (config.screen.width - 122, 20))

    if instructions:
        inst = small_font.render(
            "ARROWS/A/D:MOVE  SPACE/W:JUMP  ESC:QUIT", True, config.colors["BLACK"]
        )
        screen.blit(inst, (10, 85))


def draw_pixelated_fade(screen, fade_level, config, grid=4):
    """Draw a pixelated fade-to-black effect overlay."""
    if fade_level <= 0:
        return
    alpha = min(fade_level, 255)
    block_size = grid
    overlay = pygame.Surface((config.screen.width, config.screen.height), pygame.SRCALPHA)
    for y in range(0, config.screen.height, block_size):
        for x in range(0, config.screen.width, block_size):
            if (x // block_size + y // block_size) % 3 != 0:
                pygame.draw.rect(
                    overlay, (0, 0, 0, min(alpha // 2, 128)), (x, y, block_size, block_size)
                )
            else:
                pygame.draw.rect(
                    overlay, (0, 0, 0, min(alpha, 200)), (x, y, block_size, block_size)
                )
    screen.blit(overlay, (0, 0))
