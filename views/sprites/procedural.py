"""
views/sprites/procedural.py — генератор пиксельных спрайтов (ФР-2).

Гибридный подход (вариант C):
  - Герой/враги: текстовые ASCII-карты, где символ = цвет из палитры.
  - Монеты/тайлы: алгоритмические фигуры (круг, прямоугольник).

ProceduralSpriteSource реализует SpriteSource, поэтому может регистрироваться
в SpriteCache через register_source() без изменения логики рендера.
Все кадры строятся через pygame.Surface (не требует дисплея).
"""

import pygame

# ---------------------------------------------------------------------------
# Палитра-маппер: символ ASCII-карты -> цвет (логические имена/альтернатива)
# ---------------------------------------------------------------------------

# Символ -> цвет (используем config.colors при наличии, иначе дефолты).
# Ключи — символы, которые встречаются в картах. "." — прозрачный.
_PALETTE = {
    "H": (255, 220, 120),  # голова (кожа)
    "E": (40, 40, 40),  # глаза
    "B": (20, 90, 200),  # тело (синий "комбинезон")
    "A": (220, 60, 40),  # акцент (пояс)
    "L": (60, 60, 60),  # ноги/ботинки
    "G": (30, 160, 60),  # враг зелёный
    "Y": (200, 160, 40),  # враг жёлтый
    "K": (10, 10, 10),  # тёмный (очки врага и т.п.)
    "W": (240, 240, 240),  # белый (блик)
}


def _resolve_color(symbol: str, config_colors: dict) -> tuple[int, int, int]:
    """Возвращает цвет по символу с опорой на config.colors (если задан)."""
    if symbol == ".":
        # прозрачный — специальный случай; не рисуем
        return (0, 0, 0)
    # Названия цветов: попробуем в конфиге по имени, иначе — палитра по умолчанию.
    # Для простоты ФР-2 сначала используем _PALETTE; config-перекрытие — доп. шаг.
    return _PALETTE.get(symbol, (255, 255, 255))


# ---------------------------------------------------------------------------
# ASCII-карты (символ = пиксель)
# ---------------------------------------------------------------------------
# --- ASCII-карты (символ = пиксель; карта = list[str] из рядов-строк) ---
_HERO_IDLE: list[str] = [
    "..HHHH..",
    ".HEEEH..",
    ".HEEEH..",
    "..HHHH..",
    "..BBBB..",
    ".BBBBBB.",
    "..BABB..",
    "..BBBB..",
    "..LL.LL.",
    ".LLL.LL.",
]

_HERO_RUN_1: list[str] = [
    "..HHHH..",
    ".HEEEH..",
    ".HEEEH..",
    "..HHHH..",
    "..BBBB..",
    ".BBBBBB.",
    "..BABB..",
    "..BBBB..",
    "..LL..LL",
    "L.LL..L.",
]

_HERO_RUN_2: list[str] = [
    "..HHHH..",
    ".HEEEH..",
    ".HEEEH..",
    "..HHHH..",
    "..BBBB..",
    ".BBBBBB.",
    "..BABB..",
    "..BBBB..",
    ".LL..LL.",
    ".LL..LL.",
]

_WALKER_IDLE: list[str] = [
    "..GGGG..",
    "G.KGGK.G",
    "G.KGGK.G",
    "..GGGG..",
    ".GGGGGG.",
    "GGGGGGGG",
    ".GG..GG.",
]


def render_grid(grid: list[str], scale: int = 1) -> pygame.Surface:
    h = len(grid)
    w = len(grid[0]) if grid else 0
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            color = _resolve_color(ch, {})
            pygame.draw.rect(surf, color, (x * scale, y * scale, scale, scale))
    return surf


def _make_anim_by_poses(poses: list[list[str]], scale: int) -> list[pygame.Surface]:
    return [render_grid(p, scale) for p in poses]


# ---------------------------------------------------------------------------
# ProceduralSpriteSource
# ---------------------------------------------------------------------------

_PLAYER_POSES: list[list[str]] = [_HERO_IDLE, _HERO_RUN_1, _HERO_RUN_2]


class ProceduralSpriteSource:
    """Генерирует пиксельные кадры из ASCII-карт + фигур (ГФР-2).

    Реализует SpriteSource. supports() отвечает True для ключей, которые
    умеет генерировать (player_*, enemy_walk, coin, tile).
    """

    _SUPPORTED = (
        "player_idle",
        "player_run/left",
        "player_run/right",
        "player_jump",
        "enemy_walk",
        "coin",
        "tile",
    )

    def __init__(self, config, scale: int = 2):
        self._cfg = config
        self._scale = scale
        # размер героя = (ширина карты * scale, высота карты * scale)
        base_w = len(_HERO_IDLE[0])
        base_h = len(_HERO_IDLE)
        self._size = (base_w * scale, base_h * scale)

    def size(self) -> tuple[int, int]:
        return self._size

    def supports(self, key: str) -> bool:
        return key in self._SUPPORTED

    def frames(self, key: str, frame_count: int) -> list[pygame.Surface]:
        if not self.supports(key):
            raise KeyError(f"ProceduralSpriteSource не поддерживает '{key}'")
        if key.startswith("player"):
            return _make_anim_by_poses(
                _PLAYER_POSES, self._scale
            )  # уже ок, если _PLAYER_POSES аннотирован
        if key == "enemy_walk":
            poses: list[list[str]] = [_WALKER_IDLE]
            return _make_anim_by_poses(poses, self._scale)
        if key == "coin":
            return [self._make_coin()]
        if key == "tile":
            return [self._make_tile()]
        return []

    # --- алгоритмические фигуры (монета, тайл) ---
    def _make_coin(self) -> pygame.Surface:
        base = 16 * self._scale
        surf = pygame.Surface((base, base), pygame.SRCALPHA)
        cx = cy = base // 2
        r = (base // 2) - 1
        pygame.draw.circle(surf, (255, 200, 0), (cx, cy), r)  # золото
        pygame.draw.circle(
            surf, (255, 240, 100), (cx - 2 * self._scale, cy - 2 * self._scale), r // 2
        )  # блик
        return surf

    def _make_tile(self) -> pygame.Surface:
        size = 32 * self._scale
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        top = (30, 160, 60)
        dark = (20, 90, 40)
        pygame.draw.rect(surf, dark, (0, 0, size, size))
        pygame.draw.rect(surf, top, (0, 0, size, max(1, size // 4)))
        return surf
