"""config.py -- Load and parse settings from JSON."""
import json
import pathlib
from dataclasses import dataclass, field
from typing import Tuple, Dict, List

# --- Data Classes ---


@dataclass
class ScreenConfig:
    width: int = 800
    height: int = 600
    fps: int = 60
    caption: str = "Jump & Reach the Flag"


@dataclass
class PhysicsConfig:
    gravity: float = 900.0
    jump_strength: float = -600.0
    max_fall: float = 2000.0


@dataclass
class DeathConfig:
    """Параметры кинематографичной смерти-падения игрока (R5)."""
    gravity: float = 1200.0
    launch_vy: float = -400.0
    fall_vy: float = -100.0
    margin: int = 60


@dataclass
class PlayerConfig:
    width: int = 40
    height: int = 50
    speed: float = 350.0
    spawn: List[int] = field(default_factory=lambda: [50, 400])


@dataclass
class EnemyConfig:
    width: int = 35
    height: int = 35
    speed: float = 150.0


@dataclass
class GameConfig:
    lives: int = 3
    coins_total: int = 5
    death_respawn_offset: int = 60
    fade_speed: int = 255


@dataclass
class AssetsConfig:
    fonts_dir: str = "assets/fonts"
    sprites_dir: str = "assets/sprites"
    sounds_dir: str = "assets/sounds"
    font_size: int = 24
    small_font_size: int = 12
    font_name: str = "PressStart2P-Regular.ttf"
    bgm_file: str = "bgm_song.ogg"


@dataclass
class AnimationConfig:
    """Тайминги анимаций в СЕКУНДАХ (задержка между кадрами)."""
    idle_delay: float = 0.167      # ~10 кадров/с (было 10 тиков)
    run_delay: float = 0.10        # ~10 кадров/с (было 6 тиков)
    jump_delay: float = 0.13       # ~8 кадров/с  (было 8 тиков)
    walk_delay: float = 0.13       # ~8 кадров/с  (было 8 тиков)


@dataclass
class CollisionConfig:
    """Параметры системы коллизий."""
    fall_buffer: int = 30


class Settings:
    def __init__(self, path="config/settings.json"):
        full_path = pathlib.Path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"Config file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Загрузка базовых секций
        self.screen = ScreenConfig(**data.get("screen", {}))
        self.physics = PhysicsConfig(**data.get("physics", {}))
        self.death = DeathConfig(**data.get("death", {}))
        self.player = PlayerConfig(**data.get("player", {}))
        self.enemy = EnemyConfig(**data.get("enemy", {}))
        self.game = GameConfig(**data.get("game", {}))
        self.assets = AssetsConfig(**data.get("assets", {}))
        self.animation = AnimationConfig(**data.get("animation", {}))
        self.collision = CollisionConfig(**data.get("collision", {}))

        # Парсинг цветов (Возвращает словарь)
        self.colors = self._parse_colors(data.get("colors", {}))

    @staticmethod
    def _parse_colors(raw_colors: dict) -> Dict[str, Tuple[int, int, int]]:
        parsed = {}
        for name, color_str in raw_colors.items():
            try:
                # Убираем пробелы и разделяем по запятой
                r, g, b = map(int, color_str.replace(" ", "").split(","))
                parsed[name] = (r, g, b)
            except ValueError:
                pass
        return parsed


# Экземпляр настроек по умолчанию
settings = Settings()