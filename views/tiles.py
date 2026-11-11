"""Tiles -- merged RetroTiles (from retro_graphics.py) and TileFactory
(from retro_tiles.py). Both generators are preserved verbatim so no visual
variation is lost.
"""

import random

import pygame


class RetroTiles:
    """Original 90s-style grass/dirt platform generator (retro_graphics)."""

    @staticmethod
    def grass_top(width, height):
        surf = pygame.Surface((width, height))
        dirt = (150, 96, 40)
        dirt_dark = (110, 70, 28)
        dirt_light = (170, 110, 50)
        surf.fill(dirt)
        random.seed(42)
        for _ in range(width * height // 12):
            x = random.randint(0, width - 1)
            y = random.randint(height // 3, height - 1)
            c = random.choice([dirt_dark, dirt_light, dirt_dark])
            surf.set_at((x, y), c)
        grass_h = 10
        grass = (68, 192, 52)
        grass_light = (92, 220, 64)
        grass_dark = (40, 140, 36)
        outline = (24, 88, 28)
        pygame.draw.rect(surf, grass, (0, 0, width, grass_h))
        pygame.draw.rect(surf, grass_light, (0, 0, width, 3))
        for x in range(2, width, 6):
            blade = random.choice([grass_light, grass, grass])
            pygame.draw.rect(surf, blade, (x, 0, 2, 4))
        pygame.draw.rect(surf, grass_dark, (0, grass_h - 2, width, 2))
        pygame.draw.rect(surf, outline, (0, 0, 2, height))
        pygame.draw.rect(surf, outline, (width - 2, 0, 2, height))
        return surf

    @staticmethod
    def floating_platform(width, height):
        surf = pygame.Surface((width, height))
        surf.fill((140, 90, 40))
        random.seed(7)
        for _ in range(width * height // 8):
            x = random.randint(2, width - 3)
            y = random.randint(2, height - 3)
            surf.set_at((x, y), random.choice([(110, 65, 30), (170, 110, 55)]))
        top_h = 6
        pygame.draw.rect(surf, (40, 150, 45), (0, 0, width, top_h))
        pygame.draw.rect(surf, (70, 200, 60), (0, 0, width, 2))
        pygame.draw.rect(surf, (20, 70, 25), (0, 0, width, top_h), 1)
        pygame.draw.rect(surf, (60, 35, 15), (0, 0, width, height), 1)
        return surf


class TileFactory:
    """Second (alternative) tile style from retro_tiles.py, kept for reuse."""

    @staticmethod
    def grass_top_tile(width, height, tile_w=32):
        surf = pygame.Surface((width, height))
        dirt_color = (140, 90, 40)
        dirt_dark = (100, 65, 30)
        surf.fill(dirt_color)
        for x in range(0, width, 8):
            for y in range(height // 2, height, 8):
                if (x + y) % 3 == 0:
                    surf.fill(dirt_dark, (x + 2, y + 2, 4, 4))
                if (x + y * 2) % 5 == 0:
                    surf.fill((110, 75, 35), (x, y + 4, 6, 3))
        grass_color = (0, 200, 0)
        grass_light = (0, 220, 0)
        grass_dark = (0, 120, 0)
        outline = (0, 70, 30)
        grass_h = 12
        pygame.draw.rect(surf, outline, (0, 0, width, grass_h))
        pygame.draw.rect(surf, grass_color, (1, 1, width - 2, grass_h - 2))
        pygame.draw.rect(surf, grass_light, (1, 1, width - 2, 4))
        pygame.draw.rect(surf, grass_light, (0, 0, width, 3))
        pygame.draw.rect(surf, grass_dark, (0, grass_h - 2, width, 2))
        for x in range(4, width, 16):
            pygame.draw.rect(surf, grass_light, (x, 0, 8, 3))
            pygame.draw.rect(surf, grass_color, (x + 2, 0, 4, 4))
        return surf

    @staticmethod
    def brick_tile(width, height):
        surf = pygame.Surface((width, height))
        brick_color = (200, 80, 40)
        mortar = (120, 40, 20)
        surf.fill(brick_color)
        brick_h = 16
        for row in range(0, height, brick_h):
            offset = (row // brick_h) % 2 * 16
            for x in range(-offset, width, 32):
                pygame.draw.rect(surf, mortar, (x, row, 32, brick_h), 2)
        pygame.draw.rect(surf, (230, 110, 60), (0, 0, width, 2))
        return surf
