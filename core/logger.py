"""GameLogger -- централизованное логирование.

Пишет и в консоль (с цветом по уровню), и в файл.
Синглтон: реально один экземпляр через __new__.
Может подписываться на EventBus и логировать игровые события.
"""
import sys
import traceback
from enum import IntEnum
from datetime import datetime
from pathlib import Path


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

    @property
    def label(self):
        return self.name   # "DEBUG", "INFO", ...


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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, level=LogLevel.DEBUG, log_dir=None):
        # Инициализация выполняется один раз (как у синглтонов)
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.level = level

        # Каталог для лог-файла (по умолчанию <проект>/logs)
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent.parent / "logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Файл логов: logs/game_TIMESTAMP.log
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"game_{ts}.log"

        # Буфер событий (если понадобится собрать историю)
        self.events = []

        # Кодовая точка создания логгера
        self._log(LogLevel.INFO, "Logger", f"Logger started -> {self.log_file}")

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
            "score_changed": ("Game", "Score -> {0}"),
            "lives_changed": ("Game", "Lives -> {0}"),
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

    @staticmethod
    def _make_handler(source, template):
        """Возвращает функцию-обработчик события, форматирующую шаблон."""

        def handler(*args, **kwargs):
            # Собираем позиционные аргументы в строку
            if args and len(args) == 1:
                value = args[0]
            else:
                value = ", ".join(str(a) for a in args)
            msg = template.format(value)
            logger.info(source, msg)

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


# ----------------------------------------------------------------------
# Модульный «синглтон» — единый объект на всё приложение
# ----------------------------------------------------------------------
logger = GameLogger()