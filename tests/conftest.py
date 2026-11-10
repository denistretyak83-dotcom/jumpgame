"""Фикстуры pytest: безопасный headless-режим для pygame.

Устанавливает dummy-драйверы SDL ДО импорта pygame и инициализирует pygame
разово в начале сессии (scope="session"), а в конце корректно завершает.
Это позволяет тестам, которые импортируют модули pygame (entity, factory),
работать в CI без дисплея и без xvfb.
"""
import os

# Устанавливаем dummy-драйверы ДО любого импорта pygame.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _headless_pygame():
    """Инициализирует pygame один раз на сессию (autouse)."""
    import pygame

    pygame.init()
    yield
    pygame.quit()
