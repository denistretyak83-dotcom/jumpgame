"""GameOverHandler -- сервис экрана Game Over (фейд и рестарт по R).

Выносит из Game ответственность за:
  - переход в состояние Game Over (установка флага, событие GAME_OVER, начало фейда),
  - пиксельный фейд (fade_level / fade_direction, скорость из config.game.fade_speed),
  - рестарт игры по клавише R (делегируется обратно в Game через колбэк).

Game остаётся тонким оркестратором: в ветке GAME_OVER вызывает
game_over_handler.update(dt, keys) и, если вернулось True (рестарт), прерывает
кадр. Сервис не трогает state/рендер/камеру — только флаг game_over, фейд и
сигнал рестарта через переданный колбэк.
"""

import pygame

from core.event_bus import GameEvents


class GameOverHandler:
    """Управляет экраном Game Over: фейдом и рестартом по R."""

    def __init__(self, config, event_bus, reset_run_state):
        self._config = config  # config.game.fade_speed
        self._event_bus = event_bus
        self._reset_run_state = reset_run_state  # Callable[[], None]

        # Состояние фейда и флага — живёт здесь (Game читает через прокси).
        self.fade_level = 0
        self.fade_direction = 0
        self.game_over = False

    # ------------------------------------------------------------------
    # Вход в Game Over (вызывается Game при исчерпании жизней)
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Объявить game over: установить флаг, эмитнуть событие, начать фейд."""
        self.game_over = True
        self._event_bus.emit(GameEvents.GAME_OVER)
        self.fade_direction = 1

    # ------------------------------------------------------------------
    # Основной метод: обработка кадра состояния Game Over
    # ------------------------------------------------------------------
    def update(self, dt, keys) -> bool:
        """Обработать кадр экрана Game Over.

        Возвращает:
          - True, если нажата R -> рестарт выполнен (Game должен прервать кадр);
          - False, если кадр обработан (продолжаем фейд или ничего).
        """
        if keys[pygame.K_r]:
            self._handle_restart()
            return True
        if self.game_over:
            self._update_fade(dt)
        return False

    # ------------------------------------------------------------------
    def _handle_restart(self) -> None:
        """Рестарт по R: сбросить собственное состояние и делегировать Game."""
        self.reset()
        self._reset_run_state()

    def _update_fade(self, dt) -> None:
        """Пиксельный фейд: наращиваем fade_level до 255, затем стоп."""
        if self.fade_direction == 1:
            self.fade_level += self._config.game.fade_speed * dt
            if self.fade_level >= 255:
                self.fade_level = 255
                self.fade_direction = 0

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Сбросить состояние game over и фейда (при любом рестарте/загрузке)."""
        self.game_over = False
        self.fade_level = 0
        self.fade_direction = 0
