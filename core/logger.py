"""GameLogger -- централизованное логирование с ротацией лог-файлов.

Пишет и в консоль (с цветом по уровню), и в файл.
НЕ синглтон (R3): является обычным классом, получающим настройки через DI.
При старте удаляет лог-файлы, старше max_age_days, и удерживает максимум
max_files файлов (решение проблемы бесконечного накопления логов).
"""

import time
import traceback
from contextlib import suppress
from datetime import datetime
from enum import IntEnum
from pathlib import Path

from .config import LogConfig

# Безопасный импорт GameEvents (ПАТЧ 1): logger может грузиться первым
try:
    from core.event_bus import GameEvents

    SCORE_EVENT = GameEvents.SCORE_CHANGED
    LIVES_EVENT = GameEvents.LIVES_CHANGED
except ImportError:
    SCORE_EVENT = "score_changed"
    LIVES_EVENT = "lives_changed"


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

    @property
    def label(self):
        return self.name  # "DEBUG", "INFO", ...


# ANSI-цвета для консоли
class _Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


# Цвет уровня: DEBUG синий, INFO зелёный, WARNING жёлтый, ERROR красный
_LEVEL_COLOR = {
    LogLevel.DEBUG: _Color.BLUE,
    LogLevel.INFO: _Color.GREEN,
    LogLevel.WARNING: _Color.YELLOW,
    LogLevel.ERROR: _Color.RED,
}


class GameLogger:
    # УБРАНО: __new__, _instance, синглтон.

    def __init__(self, level=LogLevel.DEBUG, config: LogConfig | None = None):
        self.level = level
        # DI: настройки приходят из конфига, а не хардкодятся
        self.config = config or LogConfig()

        # Каталог логов (из конфигурации)
        self.log_dir = Path(self.config.log_dir)
        if not self.log_dir.is_absolute():
            self.log_dir = Path(__file__).resolve().parent.parent / self.log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # РОТАЦИЯ: очистка старых файлов ПЕРЕД созданием нового
        self._rotate_logs()

        # Файл логов: logs/game_TIMESTAMP.log
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"game_{ts}.log"
        self.events = []

    def _rotate_logs(self):
        """Удаляет файлы game_*.log старше max_age_days и удерживает max_files шт."""
        if not self.log_dir.is_dir():
            return
        files = sorted(self.log_dir.glob("game_*.log"))
        now = time.time()

        # 1) Удаление по возрасту
        for path in files:
            age_days = (now - path.stat().st_mtime) / 86400.0
            if age_days > self.config.max_age_days:
                with suppress(OSError):
                    path.unlink()

        # 2) Предохранитель по количеству (удаляем самые старые)
        files = sorted(self.log_dir.glob("game_*.log"))
        while len(files) > self.config.max_files:
            with suppress(OSError):
                files[0].unlink()
            files = sorted(self.log_dir.glob("game_*.log"))

    # ------------------------------------------------------------------
    # Основной метод записи
    # ------------------------------------------------------------------
    def _log(self, level, source, message):
        if level.value < self.level.value:
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] [{level.label:<7}] [{source}] {message}"

        # 1. Консоль (с цветом для ERROR/WARNING и т.д.)
        color = _LEVEL_COLOR.get(level, _Color.RESET)
        print(f"{color}{line}{_Color.RESET}")

        # 2. Файл (без цвета, в чистом виде)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError as e:
            print(f"{_Color.RED}[Logger] Ошибка записи в файл: {e}{_Color.RESET}")

    # ------------------------------------------------------------------
    # Публичные методы по уровням
    # ------------------------------------------------------------------
    def debug(self, source, message):
        self._log(LogLevel.DEBUG, source, message)

    def info(self, source, message):
        self._log(LogLevel.INFO, source, message)

    def warning(self, source, message):
        self._log(LogLevel.WARNING, source, message)

    def error(self, source, message, exc=False):
        self._log(LogLevel.ERROR, source, message)
        if exc:
            self._log(LogLevel.ERROR, source, traceback.format_exc())

    # ------------------------------------------------------------------
    # Связь с EventBus: подписка на события игры
    # ------------------------------------------------------------------
    def attach(self, event_bus, extra=None):
        """Подписывает Logger на события EventBus и логирует их.

        extra: dict {event_name: (source, template)}, где template использует {0},{1}...
        """
        if event_bus is None:
            self.warning("Logger", "EventBus is None, skip attach")
            return

        # Базовые события, которые точно есть в игре
        known = {
            SCORE_EVENT: ("Game", "Score -> {0}"),
            LIVES_EVENT: ("Game", "Lives -> {0}"),
        }

        # Дополнительные из внешего кода
        if extra:
            known.update(extra)

        for event_name, (source, template) in known.items():
            try:
                # callback принимает позиционный аргумент/аргументы события
                event_bus.subscribe(event_name, self._make_handler(source, template))
                self.debug("Logger", f"Subscribed to event: {event_name}")
            except Exception as e:
                self.warning("Logger", f"Cannot subscribe to {event_name}: {e}")

    def _make_handler(self, source, template):
        """Обработчик пишет в ТОТ же логгер, на котором вызван attach() (DI)."""

        def handler(*args, **kwargs):
            value = args[0] if args and len(args) == 1 else ", ".join(str(a) for a in args)
            msg = template.format(value)
            self.info(source, msg)  # ← self, не глобальный logger

        return handler

    # ------------------------------------------------------------------
    # Служебное: пометка ключевых моментов
    # ------------------------------------------------------------------
    def start_level(self, level_name):
        self.info("LevelManager", f"Loading level: {level_name}")

    def game_event(self, event_name, **details):
        """Логирует произвольное игровое событие."""
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        self.info("Event", f"{event_name} [ {detail_str} ]")
