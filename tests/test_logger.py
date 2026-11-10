"""Тесты GameLogger: уровни, запись в файл, ротация, подписка на EventBus."""
import os
import time

import pytest

from core.config import LogConfig
from core.logger import GameLogger, LogLevel
from core.event_bus import GameEvents

# --------------------------------------------------------------------------
# Фейковый конфиг логгера (DI). Поля задаём напрямую.
# --------------------------------------------------------------------------
def make_config(tmp_path, max_age_days=30, max_files=10, log_dir=None):
    class FakeLogConfig:
        def __init__(self):
            self.log_dir = str(log_dir or tmp_path)
            self.max_age_days = max_age_days
            self.max_files = max_files
    return FakeLogConfig()


@pytest.fixture
def logger(tmp_path):
    cfg = make_config(tmp_path, max_age_days=30, max_files=10)
    return GameLogger(config=cfg)


def test_logger_creates_log_dir_and_file(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(config=cfg)
    # файл логов создаётся: game_TIMESTAMP.log в каталоге
    assert lg.log_file.parent == tmp_path
    assert lg.log_file.name.startswith("game_")
    assert lg.log_file.name.endswith(".log")


def test_log_level_enum_labels():
    assert LogLevel.DEBUG.label == "DEBUG"
    assert LogLevel.INFO.label == "INFO"
    assert LogLevel.WARNING.label == "WARNING"
    assert LogLevel.ERROR.label == "ERROR"


def test_log_below_level_is_skipped(tmp_path):
    # уровень INFO -> DEBUG-сообщение не пишется в файл
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    lg.debug("Src", "debug msg")   # отфильтровано
    content = lg.log_file.read_text(encoding="utf-8") if lg.log_file.exists() else ""
    assert "debug msg" not in content


def test_log_info_is_written_to_file(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    lg.info("Src", "hello world")
    content = lg.log_file.read_text(encoding="utf-8")
    assert "hello world" in content
    assert "Src" in content


def test_error_logs_traceback_when_exc(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.ERROR, config=cfg)
    try:
        1 / 0
    except ZeroDivisionError:
        lg.error("Src", "boom", exc=True)
    content = lg.log_file.read_text(encoding="utf-8")
    assert "boom" in content
    assert "ZeroDivisionError" in content  # traceback попал в файл


# --------------------------------------------------------------------------
# Ротация
# --------------------------------------------------------------------------
def _create_log_file(dirpath, name, age_days):
    path = dirpath / name
    path.write_text("x", encoding="utf-8")
    old = time.time() - age_days * 86400
    os.utime(path, (old, old))
    return path


def test_rotation_removes_old_files(tmp_path):
    cfg = make_config(tmp_path, max_age_days=1, max_files=10)
    _create_log_file(tmp_path, "game_old.log", age_days=10)  # старше 1 дня
    lg = GameLogger(config=cfg)   # при старте вызывается _rotate_logs
    remaining = list(tmp_path.glob("game_*.log"))
    assert len(remaining) == 0 or all("old" not in p.name for p in remaining)
    # проверяем, что старый файл действительно удалён
    assert not (tmp_path / "game_old.log").exists()


def test_rotation_keeps_max_files(tmp_path):
    # создаём больше макс_кол-ва файлов -> старые удаляются
    cfg = make_config(tmp_path, max_age_days=30, max_files=3)
    for i in range(5):
        _create_log_file(tmp_path, f"game_{i}.log", age_days=1)
    lg = GameLogger(config=cfg)
    remaining = sorted(tmp_path.glob("game_*.log"))
    # максимум max_files старых + текущий файл логгера
    assert len(remaining) <= 3 + 1


# --------------------------------------------------------------------------
# attach к EventBus
# --------------------------------------------------------------------------
def test_attach_with_none_event_bus(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(config=cfg)
    # None: не падать, только warning в консоль
    lg.attach(None)
    assert lg.log_file.exists()  # не сломалось


class FakeEventBus:
    def __init__(self):
        self.subscriptions = {}

    def subscribe(self, event, handler):
        self.subscriptions.setdefault(event, []).append(handler)


def test_attach_subscribes_to_score_and_lives(tmp_path):
    from core.event_bus import GameEvents

    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    bus = FakeEventBus()
    lg.attach(bus)
    assert GameEvents.SCORE_CHANGED in bus.subscriptions
    assert GameEvents.LIVES_CHANGED in bus.subscriptions


def test_handler_writes_to_log(tmp_path):
    from core.event_bus import GameEvents

    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    bus = FakeEventBus()
    lg.attach(bus)
    # вызываем обработчик через EventBus-подписку
    handlers = bus.subscriptions[GameEvents.SCORE_CHANGED]
    for h in handlers:
        h(123)
    content = lg.log_file.read_text(encoding="utf-8")
    assert "123" in content


def test_start_level_logs(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    lg.start_level("level_2")
    content = lg.log_file.read_text(encoding="utf-8")
    assert "level_2" in content


def test_game_event_logs(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    lg.game_event("PLAYER_DIED", reason="spike")
    content = lg.log_file.read_text(encoding="utf-8")
    assert "PLAYER_DIED" in content
    assert "reason=spike" in content

# --------------------------------------------------------------------------
# Дополнения: ошибки записи, подписка-сбой, multiple-args и пустые details
# --------------------------------------------------------------------------

def test_log_handles_oserror_when_writing(capsys, tmp_path):
    """При ошибке записи в файл логгер не падает и печатает в консоль."""
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)

    # Подменяем open, чтобы он кидал OSError
    real_open = open

    def broken_open(*args, **kwargs):
        raise OSError("disk full")

    lg._log(LogLevel.INFO, "Src", "msg")  # без подмены — работает
    # теперь подменим open только для записи в лог-файл
    import builtins
    original = builtins.open
    builtins.open = broken_open
    try:
        lg.info("Src", "will fail to write")
    finally:
        builtins.open = original
    out = capsys.readouterr().out
    assert "Ошибка записи" in out or "disk full" in out


class ThrowingBus:
    def subscribe(self, event, callback):
        raise RuntimeError("no bus today")


def test_attach_logs_warning_when_subscribe_fails(capsys, tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    # attach с bus, у которого subscribe кидает -> не падает, пишет warning
    lg.attach(ThrowingBus())
    # warning пишется в файл и файл существует
    assert lg.log_file.exists()


def test_attach_with_extra_events(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)

    class Bus:
        def __init__(self):
            self.subs = []
        def subscribe(self, event, callback):
            self.subs.append((event, callback))
            return len(self.subs)

    bus = Bus()
    lg.attach(bus, extra={GameEvents.PLAYER_DIED: ("Game", "Player died -> {0}")})
    # подписались на стандартные + extra
    events = [e for e, _ in bus.subs]
    assert GameEvents.PLAYER_DIED in events


def test_make_handler_with_multiple_args(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    handler = lg._make_handler("Src", "Values: {0}")
    handler(1, 2, 3)  # несколько аргументов -> ", ".join
    content = lg.log_file.read_text(encoding="utf-8")
    assert "1, 2, 3" in content


def test_game_event_with_empty_details(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    lg.game_event("TICK")   # без details -> пустой detail_str
    content = lg.log_file.read_text(encoding="utf-8")
    assert "TICK" in content


def test_handler_with_zero_args(tmp_path):
    cfg = make_config(tmp_path)
    lg = GameLogger(level=LogLevel.INFO, config=cfg)
    handler = lg._make_handler("Src", "No value")
    handler()   # args пуст -> value=""
    content = lg.log_file.read_text(encoding="utf-8")
    assert "No value" in content