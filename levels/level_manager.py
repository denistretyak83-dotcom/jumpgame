"""LevelManager -- loads / builds / caches levels from JSON."""

import json
import logging
import pathlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from core.geometry import RectPosition

logger = logging.getLogger(__name__)


@dataclass
class LevelData:
    """Структурированный результат загрузки уровня."""

    name: str
    next_level: str | None
    player_spawn: tuple[float, float]
    platforms: list[RectPosition]
    coins: list[RectPosition]
    enemies: list[Any]
    flag_rect: RectPosition


class LevelBuilder:
    """Собирает LevelData из сырого JSON, используя factories."""

    def __init__(self, entity_factories: dict[str, Callable]):
        # entity_factories: {"platform": factory_func, "coin": factory_func, ...}
        self.factories = entity_factories

    def build(self, raw: dict[str, Any]) -> LevelData:
        # Валидация базовых ключей
        required = {"player_spawn", "platforms", "flag"}
        missing = required - raw.keys()
        if missing:
            raise ValueError(f"Level JSON missing keys: {missing}")

        spawn = (float(raw["player_spawn"]["x"]), float(raw["player_spawn"]["y"]))
        flag = self.factories["flag"](raw["flag"])

        # Парсим коллекции через фабрики (если ключа нет — пустой список)
        platforms = [self.factories["platform"](p) for p in raw["platforms"]]
        coins = [self.factories["coin"](c) for c in raw["coins"]]
        enemies = [self.factories["enemy"](e) for e in raw.get("enemies", [])]

        return LevelData(
            name=raw.get("name", "unknown"),
            next_level=raw.get("next_level"),
            player_spawn=spawn,
            platforms=platforms,
            coins=coins,
            enemies=enemies,
            flag_rect=flag,
        )


class LevelManager:
    """Тонкий слой: читает JSON, делегирует билдеру, кеширует результаты."""

    def __init__(self, project_root: pathlib.Path, entity_factories: dict[str, Callable]):
        self.project_root = project_root
        self.levels_dir = project_root / "levels"
        self.builder = LevelBuilder(entity_factories)
        self._cache: dict[str, LevelData] = {}

    def _resolve_path(self, name: str) -> pathlib.Path:
        if not name.endswith(".json"):
            name += ".json"
        path = self.levels_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Level not found: {path}")
        return path

    def load_level(self, level_name: str) -> LevelData:
        if level_name in self._cache:
            return self._cache[level_name]

        path = self._resolve_path(level_name)
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse {path}: {e}") from e

        logger.info(f"Loading level: {level_name}")
        level_data = self.builder.build(raw)
        self._cache[level_name] = level_data
        return level_data

    def clear_cache(self, level_name: str | None = None) -> None:
        if level_name:
            self._cache.pop(level_name, None)
        else:
            self._cache.clear()
