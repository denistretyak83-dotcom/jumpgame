"""SpriteCache -- централизованный View-слой для анимаций сущностей.

Загружает спрайты из ассетов через AssetLoader и создаёт CharacterView
для игрока и врагов. Развязывает модель и картинки: модель отдаёт
только логические ключи анимации (see CharacterVisualState).

Анимации размечаются ЛОГИЧЕСКИМИ ключами:
  player: idle, run_left, run_right, jump
  enemy:  walk
"""
from views.character_view import CharacterView


class SpriteCache:
    """Содержит CharacterView для каждого типа сущности."""

    def __init__(self, asset_loader, config):
        """
        Args:
            asset_loader: core.asset_loader.AssetLoader (загружает PNG-кадры).
            config: core.config.settings (размеры спрайтов).
        """
        self._assets = asset_loader
        self._cfg = config
        self._player_view = None
        self._enemy_view = None

    # ------------------------------------------------------------------
    # Публичный доступ к View для сущностей
    # ------------------------------------------------------------------

    def player_view(self) -> CharacterView:
        """Возвращает (и кэширует) CharacterView игрока."""
        if self._player_view is None:
            self._player_view = CharacterView(self._build_player_animations())
        return self._player_view

    def enemy_view(self) -> CharacterView:
        """Возвращает (и кэширует) CharacterView врага."""
        if self._enemy_view is None:
            self._enemy_view = CharacterView(self._build_enemy_animations())
        return self._enemy_view

    # ------------------------------------------------------------------
    # Сборка анимаций из ассетов
    # ------------------------------------------------------------------

    def _build_player_animations(self) -> dict:
        anim = self._cfg.animation
        psize = (self._cfg.player.width, self._cfg.player.height)

        jump_all = self._assets.load_animation_frames("player_jump", 2, psize)
        jump_neutral = jump_all[0:1] if jump_all else []
        jump_directed = jump_all[1:2] if jump_all else []

        from views.animation import Animation
        return {
            'idle': Animation(
                self._assets.load_animation_frames("player_idle", 3, psize),
                anim.idle_delay),
            'run_left': Animation(
                self._assets.load_animation_frames("player_run/left", 4, psize),
                anim.run_delay),
            'run_right': Animation(
                self._assets.load_animation_frames("player_run/right", 4, psize),
                anim.run_delay),
            'jump_neutral': Animation(jump_neutral, anim.jump_delay, loop=False),
            'jump': Animation(jump_directed, anim.jump_delay, loop=False),
        }

    def _build_enemy_animations(self) -> dict:
        anim = self._cfg.animation
        esize = (self._cfg.enemy.width, self._cfg.enemy.height)
        walk_frames = self._assets.load_animation_frames("enemy_walk", 4, esize)

        from views.animation import Animation
        return {
            'walk': Animation(walk_frames, anim.walk_delay),
        }

    def update(self, dt: float):
        """Продвигает все анимации на dt секунд (вызывается каждый кадр)."""
        for view in (self._player_view, self._enemy_view):
            if view is None:
                continue
            for anim in view.animations.values():
                if anim is not None:
                    anim.update(dt)  # теперь dt реально используется
