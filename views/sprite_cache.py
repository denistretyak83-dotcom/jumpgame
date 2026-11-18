"""SpriteCache -- централизованный View-слой для анимаций сущностей.

Загружает кадры из SpriteSource (PNG или procedural) и создаёт CharacterView
для игрока и врагов. Развязывает модель и картинки: модель отдаёт только
логические ключи анимации CharacterView.build_state.

Реестр источников (OCP): SpriteCache работает с абстракцией SpriteSource.
Default — PngSpriteSource. Новый источник (generator, ФР-2) регистрируется
через register_source() без изменения логики рендера.

Анимации размечаются ЛОГИЧЕСКИМИ ключами:
  player: idle, run_left, run_right, jump
  enemy:  walk
"""

from views.animation import Animation
from views.character_view import CharacterView
from views.sprites.sprite_source import PngSpriteSource, SpriteSource


class SpriteCache:
    """Содержит CharacterView для каждого типа сущности + реестр источников."""

    def __init__(self, asset_loader, config):
        """
        Args:
            asset_loader: core.asset_loader.AssetLoader (загружает PNG-кадры).
            config: core.config.settings (размеры спрайтов).
        """
        self._assets = asset_loader
        self._cfg = config
        self._player_view = None
        self._enemy_views = {}  # кэш вью врагов по sprite_key

        # --- Реестр источников кадров (ФР-1, OCP) ---
        self._sources: dict[str, SpriteSource] = {
            "png": PngSpriteSource(asset_loader, config),
        }
        self._default_source = "png"

    # ------------------------------------------------------------------
    # Управление источниками (ФР-1)
    # ------------------------------------------------------------------
    def register_source(self, name: str, source: SpriteSource) -> None:
        """OCP: регистрирует новый источник кадров (generator и т.д.)."""
        self._sources[name] = source

    def set_default_source(self, name: str) -> None:
        """Устанавливает источник по умолчанию (по имени)."""
        if name not in self._sources:
            raise KeyError(f"SpriteCache: неизвестный источник '{name}'")
        self._default_source = name

    @property
    def default_source(self) -> SpriteSource:
        return self._sources[self._default_source]

    # ------------------------------------------------------------------
    # Публичный доступ к View для сущностей
    # ------------------------------------------------------------------

    def player_view(self) -> CharacterView:
        """Возвращает (и кэширует) CharacterView игрока."""
        if self._player_view is None:
            self._player_view = CharacterView(self._build_player_animations())
        return self._player_view

    def enemy_view(self, sprite_key="walker"):
        if sprite_key not in self._enemy_views:
            self._enemy_views[sprite_key] = CharacterView(self._build_enemy_animations())
        return self._enemy_views[sprite_key]

    # ------------------------------------------------------------------
    # Сборка анимаций через SpriteSource (ФР-1)
    # ------------------------------------------------------------------

    def _build_player_animations(self) -> dict:
        anim = self._cfg.animation
        src = self.default_source

        jump_all = src.frames("player_jump", 2)
        jump_neutral = jump_all[0:1] if jump_all else []
        jump_directed = jump_all[1:2] if jump_all else []

        return {
            "idle": Animation(src.frames("player_idle", 3), anim.idle_delay),
            "run_left": Animation(src.frames("player_run/left", 4), anim.run_delay),
            "run_right": Animation(src.frames("player_run/right", 4), anim.run_delay),
            "jump_neutral": Animation(jump_neutral, anim.jump_delay, loop=False),
            "jump": Animation(jump_directed, anim.jump_delay, loop=False),
        }

    def _build_enemy_animations(self) -> dict:
        anim = self._cfg.animation
        src = self.default_source
        walk_frames = src.frames("enemy_walk", 4)

        return {
            "walk": Animation(walk_frames, anim.walk_delay),
        }

    def update(self, dt: float):
        """Продвигает все анимации на dt секунд (вызывается каждый кадр)."""
        if self._player_view is not None:
            for a in self._player_view.animations.values():
                if a is not None:
                    a.update(dt)

        for view in self._enemy_views.values():
            if view is None:
                continue
            for a in view.animations.values():
                if a is not None:
                    a.update(dt)
