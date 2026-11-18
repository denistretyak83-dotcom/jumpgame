"""
views/backgrounds/retro.py — RetroBackground (многослойный параллакс).

Реализует контракт Background. Цвета берёт из config.colors (тема, Фаза 10),
слой покрашенные без хардкода. Добавление нового слоя = добавить в _build_layers.
"""

import pygame

from core.camera import ParallaxCamera


class RetroBackground:
    """Ретро-фон: небо + горы (дальние/ближние) + облака, с параллаксом."""

    def __init__(self, screen_width, screen_height, config=None):
        self.width = screen_width
        self.height = screen_height
        # Цвета из темы (config.colors) с fallback на дефолтные.
        colors = getattr(config, "colors", {}) if config else {}
        self.sky_top = colors.get("SKY_RETRO", (108, 156, 252))
        self.sky_bottom = colors.get("SKY", (168, 200, 255))

        # Скорости параллакс-слоёв (из config или дефолт) — ДО сборки слоёв
        self.far_speed = getattr(config, "far_speed", 0.05) if config else 0.05
        self.near_speed = getattr(config, "near_speed", 0.15) if config else 0.15
        self.cloud_speed = getattr(config, "cloud_speed", 0.025) if config else 0.025

        self._layers = []
        self._build_layers()

        self.camera = ParallaxCamera(
            screen_width=self.width,
            screen_height=self.height,
        )

    # ---------------- сборка слоёв ----------------
    def _build_layers(self):
        self.mountains_far = self._make_mountains_far()
        self.mountains_near = self._make_mountains_near()
        self.clouds = self._make_cloud_layer()
        # реестр слоёв (OCP-точка: добавить слой = append в список)
        self._layers = [
            ("clouds", self.clouds, self.cloud_speed, self.width * 2, 0),
            ("far", self.mountains_far, self.far_speed, self.width, 80),
            ("near", self.mountains_near, self.near_speed, self.width, 150),
        ]

    @property
    def layers(self) -> list:
        return list(self._layers)

    # ---------------- слой конструкторы (перенесено из оригинала) ----------------
    # (вставь сюда _make_mountains_far, _make_mountains_near, _make_cloud_layer
    #  из твоего views/background.py, без изменений)

    def update(self, player_x, scroll_speed=1):
        self.camera.update(player_x)

    def draw(self, screen, player_x):
        self.camera.update(player_x)
        screen.fill(self.sky_top)

        for _name, surf, speed, repeat, y_off in self._layers:
            off = self.camera.layer_offset(speed, repeat)
            screen.blit(surf, (off, y_off))
            screen.blit(surf, (off - repeat, y_off))
            screen.blit(surf, (off + repeat, y_off))

    def _make_mountains_far(self):
        w = self.width
        surf = pygame.Surface((w * 2, 180), pygame.SRCALPHA)
        points = [
            (0, 180),
            (40, 90),
            (110, 180),
            (170, 60),
            (260, 180),
            (330, 100),
            (400, 180),
            (480, 70),
            (560, 180),
            (630, 110),
            (700, 180),
            (770, 55),
            (850, 180),
            (930, 95),
            (1000, 180),
            (1070, 70),
            (1160, 180),
            (1240, 120),
            (1320, 180),
            (1400, 60),
            (1480, 180),
            (1560, 100),
            (1650, 180),
        ]
        pygame.draw.polygon(surf, (134, 174, 224), points)
        shading = pygame.Surface((w * 2, 180), pygame.SRCALPHA)
        for peak in [(170, 60), (480, 70), (770, 55), (1070, 70), (1400, 60)]:
            xp, yp = peak
            pygame.draw.polygon(
                shading, (100, 140, 200), [(xp, yp), (xp + 90, 180), (xp + 30, 180)]
            )
        surf.blit(shading, (0, 0))
        return surf

    def _make_mountains_near(self):
        w = self.width
        surf = pygame.Surface((w * 2, 200), pygame.SRCALPHA)
        points = [
            (0, 200),
            (50, 140),
            (140, 200),
            (220, 100),
            (330, 200),
            (410, 130),
            (520, 200),
            (600, 90),
            (720, 200),
            (800, 150),
            (900, 200),
            (990, 110),
            (1100, 200),
            (1180, 145),
            (1290, 200),
            (1370, 95),
            (1480, 200),
            (1560, 135),
            (1660, 200),
        ]
        pygame.draw.polygon(surf, (76, 154, 100), points)
        for i in range(0, w * 2, 120):
            h = (i // 120) % 2
            if h == 0:
                x = i + 40
                pygame.draw.polygon(surf, (26, 96, 52), [(x, 130), (x + 12, 110), (x + 24, 130)])
                pygame.draw.rect(surf, (96, 64, 32), (x + 11, 130, 3, 10))
            else:
                x = i + 50
                pygame.draw.ellipse(surf, (46, 134, 72), (x, 140, 40, 20))
                pygame.draw.ellipse(surf, (36, 114, 62), (x + 8, 136, 30, 16))
        return surf

    def _make_cloud_layer(self):
        w = self.width
        surf = pygame.Surface((w * 2, 180), pygame.SRCALPHA)
        cloud_positions = [
            (50, 30),
            (300, 50),
            (560, 25),
            (850, 60),
            (1100, 35),
            (1350, 55),
            (1600, 30),
        ]
        for cx, cy in cloud_positions:
            pygame.draw.rect(surf, (255, 255, 255), (cx, cy + 15, 90, 14))
            pygame.draw.rect(surf, (255, 255, 255), (cx + 15, cy + 5, 60, 14))
            pygame.draw.rect(surf, (255, 255, 255), (cx + 30, cy, 30, 10))
            pygame.draw.rect(surf, (210, 225, 245), (cx, cy + 24, 90, 5))
        return surf
