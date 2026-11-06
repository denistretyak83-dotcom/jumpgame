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
        psize = (self._cfg.player.width, self._cfg.player.height)

        # player_jump: [1.png (нейтральный), 2.png (направленный)]
        jump_all = self._assets.load_animation_frames("player_jump", 2, psize)

        # Кадр 1 (index 0) -- прыжок на месте (нейтральный, без поворота)
        jump_neutral = jump_all[0:1] if jump_all else []
        # Кадр 2 (index 1) -- направленный прыжок (flip по направлению)
        jump_directed = jump_all[1:2] if jump_all else []

        from views.animation import Animation
        return {
            'idle': Animation(self._assets.load_animation_frames("player_idle", 3, psize), 10),
            'run_left': Animation(self._assets.load_animation_frames("player_run/left", 4, psize), 6),
            'run_right': Animation(self._assets.load_animation_frames("player_run/right", 4, psize), 6),
            'jump_neutral': Animation(jump_neutral, 8, loop=False),  # на месте -- кадр 1
            'jump': Animation(jump_directed, 8, loop=False),  # направленный -- кадр 2
        }

    def _build_enemy_animations(self) -> dict:
        """Собирает анимацию врага."""
        esize = (self._cfg.enemy.width, self._cfg.enemy.height)
        walk_frames = self._assets.load_animation_frames("enemy_walk", 4, esize)

        from views.animation import Animation
        return {
            'walk': Animation(walk_frames, 8),
        }

    def update(self, dt=None):
        """Продвигает все анимации на один шаг кадра.

        dt не используется (Animation.update() продвигает по frame_delay),
        но принимается для будущих временных привязок.
        Вызывается из Game каждый кадр.
        """
        for view in (self._player_view, self._enemy_view):
            if view is None:
                continue
            for anim in view.animations.values():
                if anim is not None:
                    anim.update()
