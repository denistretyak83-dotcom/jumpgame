"""Уровневая схема и мигратор данных (I1: стабилизация JSON-схемы уровней).

Согласованная схема enemy-элемента уровня:

    {
        "type": "enemy",              # тип сущности (обязательный после миграции)
        "x": int, "y": int,           # позиция спавна
        "left": int, "right": int,    # границы X-патруля
        "behavior": "...",            # поведение (walker|chaser|flyer|jumper|enemy)
        "sprite": "...",              # спрайт/анимация (опционально)
        "w": int, "h": int            # опциональное переопределение размера
    }

Мигратор переводит старый формат (без type/w/h) в новый, заполняя дефолты.
Валидатор проверяет корректность схемы и возвращает список ошибок (пустой — ок).
Все функции чистые: не мутируют входные данные и не зависят от глобального
состояния (SI/OCP-friendly).
"""

import copy

# --- Дефолты схемы (совпадают с config.enemy.width/height = 35). ---
DEFAULT_ENEMY_TYPE = "enemy"
DEFAULT_ENEMY_WIDTH = 35
DEFAULT_ENEMY_HEIGHT = 35

# Поведения, известные реестру EnemyBehavior (включая алиас "enemy" -> walker).
VALID_BEHAVIORS = {"walker", "chaser", "flyer", "jumper", "enemy"}

# Обязательные ключи enemy-элемента.
_REQUIRED_ENEMY_KEYS = ("x", "y", "left", "right")
# Опциональные ключи enemy-элемента.
_OPTIONAL_ENEMY_KEYS = ("type", "behavior", "sprite", "w", "h")


def migrate_enemy(
    enemy,
    default_w=DEFAULT_ENEMY_WIDTH,
    default_h=DEFAULT_ENEMY_HEIGHT,
    default_type=DEFAULT_ENEMY_TYPE,
):
    """Мигрировать один enemy-dict старого формата -> нового.

    Чистая функция: не меняет входной dict (работает с копией). Заполняет
    отсутствующие `type`, `w`, `h` дефолтами; сохраняет behavior/sprite/x/y/left/right.
    """
    result = copy.deepcopy(enemy)
    result.setdefault("type", default_type)
    result.setdefault("w", default_w)
    result.setdefault("h", default_h)
    return result


def migrate_level(
    level,
    default_w=DEFAULT_ENEMY_WIDTH,
    default_h=DEFAULT_ENEMY_HEIGHT,
    default_type=DEFAULT_ENEMY_TYPE,
):
    """Мигрировать уровень целиком: применить миграцию к каждому врагу.

    Возвращает новый dict уровня (входной не мутируется). Если ключа enemies
    в уровне нет — возвращает уровень без изменений (копию).
    """
    result = copy.deepcopy(level)
    if "enemies" in result:
        result["enemies"] = [
            migrate_enemy(e, default_w, default_h, default_type) for e in result["enemies"]
        ]
    return result


def validate_enemy(enemy):
    """Валидация схемы одного enemy-dict.

    Возвращает список строк-ошибок. Пустой список — враг валиден.
    """
    errors = []
    if not isinstance(enemy, dict):
        return [f"enemy должен быть dict, получен {type(enemy).__name__}"]
    for key in _REQUIRED_ENEMY_KEYS:
        if key not in enemy:
            errors.append(f"enemy: отсутствует обязательный ключ '{key}'")
    # Тип сущности (обязателен после стабилизации схемы).
    if "type" not in enemy:
        errors.append("enemy: отсутствует ключ 'type' (тип сущности)")
    # Поведение из допустимого набора (fallback walker, если не указано).
    behavior = enemy.get("behavior", "walker")
    if behavior not in VALID_BEHAVIORS:
        errors.append(
            f"enemy: неизвестное behavior '{behavior}' (допустимо: {sorted(VALID_BEHAVIORS)})"
        )
    # w/h должны быть целыми положительными числами (если заданы).
    for key in ("w", "h"):
        value = enemy.get(key)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
        ):
            errors.append(
                f"enemy: '{key}' должен быть целым положительным числом, получено {value!r}"
            )
    return errors


def validate_level(level):
    """Валидация схемы уровня целиком (по enemies и базовым ключам).

    Возвращает список строк-ошибок. Пустой список — уровень валиден.
    """
    errors = []
    if not isinstance(level, dict):
        return [f"level должен быть dict, получен {type(level).__name__}"]
    for key in ("player_spawn", "platforms", "flag"):
        if key not in level:
            errors.append(f"level: отсутствует обязательный ключ '{key}'")
    for i, enemy in enumerate(level.get("enemies", [])):
        for err in validate_enemy(enemy):
            errors.append(f"level.enemies[{i}]: {err}")
    return errors


def migrate_level_file(path, *, out_path=None):
    """(Вспомогательная) мигрировать JSON-файл уровня на диск.

    Читает path, мигрирует, и пишет результат в out_path (если задан) или
    перезаписывает path. Используется для обновления реальных level_*.json.
    Намеренно не импортируется в зависимостях уровня (только ручной запуск).
    """
    import json
    import pathlib

    p = pathlib.Path(path)
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    migrated = migrate_level(raw)
    target = pathlib.Path(out_path) if out_path else p
    with open(target, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return migrated
