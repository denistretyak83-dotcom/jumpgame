"""Тесты загрузки конфигурации через Settings (core/config.py, без pygame)."""
from pathlib import Path

from core.config import Settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"


def test_settings_loads_from_disk():
    """Settings() читает config/settings.json и заполняет секции."""
    s = Settings(str(SETTINGS_PATH))
    assert s.screen.width == 800
    assert s.screen.height == 600
    assert s.screen.fps == 60


def test_settings_has_expected_sections():
    s = Settings(str(SETTINGS_PATH))
    assert s.player.width > 0
    assert s.physics.gravity > 0
    assert s.enemy.width > 0
    assert "%" in str(s.colors) or isinstance(s.colors, dict)


def test_settings_color_parsing():
    """Цвета парсятся строкой 'r,g,b' в кортеж."""
    s = Settings(str(SETTINGS_PATH))
    blue = s.colors["BLUE"]
    assert isinstance(blue, tuple)
    assert len(blue) == 3
    assert all(isinstance(v, int) for v in blue)
