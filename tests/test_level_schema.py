"""Тесты уровневой схемы и мигратора (I1: стабилизация JSON-схемы).

Проверяем:
- миграцию старого формата enemy -> нового (type/w/h заполняются дефолтами);
- миграцию уровня целиком;
- валидацию схемы enemy и уровня (корректные и некорректные случаи);
- что `type`/`w`/`h` реально используются моделью Enemy (переопределение размера).
"""
import json
import pathlib

import pytest

from levels.level_schema import (
    DEFAULT_ENEMY_TYPE,
    DEFAULT_ENEMY_WIDTH,
    DEFAULT_ENEMY_HEIGHT,
    migrate_enemy,
    migrate_level,
    validate_enemy,
    validate_level,
)


# --------------------------------------------------------------------------
# migrate_enemy
# --------------------------------------------------------------------------
def test_migrate_enemy_fills_defaults():
    old = {"x": 100, "y": 200, "left": 0, "right": 300, "behavior": "walker", "sprite": "walker"}
    migrated = migrate_enemy(old)
    assert migrated["type"] == DEFAULT_ENEMY_TYPE == "enemy"
    assert migrated["w"] == DEFAULT_ENEMY_WIDTH == 35
    assert migrated["h"] == DEFAULT_ENEMY_HEIGHT == 35
    # исходные поля сохраняются без изменений
    assert migrated["x"] == 100
    assert migrated["y"] == 200
    assert migrated["behavior"] == "walker"
    assert migrated["sprite"] == "walker"
    # чистая функция: входной dict не мутируется
    assert "type" not in old
    assert "w" not in old
    assert "h" not in old


def test_migrate_enemy_preserves_existing_values():
    new = {"x": 100, "y": 200, "left": 0, "right": 300, "behavior": "chaser",
           "sprite": "chaser", "type": "enemy", "w": 40, "h": 60}
    migrated = migrate_enemy(new)
    assert migrated["type"] == "enemy"
    assert migrated["w"] == 40
    assert migrated["h"] == 60


def test_migrate_enemy_custom_defaults():
    old = {"x": 1, "y": 2, "left": 0, "right": 100}
    migrated = migrate_enemy(old, default_w=50, default_h=70, default_type="boss")
    assert migrated["w"] == 50
    assert migrated["h"] == 70
    assert migrated["type"] == "boss"


# --------------------------------------------------------------------------
# migrate_level
# --------------------------------------------------------------------------
def test_migrate_level_migrates_all_enemies():
    old_level = {
        "name": "L1",
        "player_spawn": {"x": 0, "y": 0},
        "platforms": [],
        "flag": {"x": 0, "y": 0},
        "enemies": [
            {"x": 1, "y": 2, "left": 0, "right": 100},
            {"x": 3, "y": 4, "left": 0, "right": 200},
        ],
    }
    migrated = migrate_level(old_level)
    assert all(e["type"] == "enemy" for e in migrated["enemies"])
    assert all(e["w"] == 35 and e["h"] == 35 for e in migrated["enemies"])
    # не вражеские поля не меняются
    assert migrated["name"] == "L1"
    assert migrated["player_spawn"] == {"x": 0, "y": 0}


def test_migrate_level_without_enemies_unchanged():
    lvl = {"name": "L", "player_spawn": {"x": 0, "y": 0}, "platforms": [], "flag": {"x": 0, "y": 0}}
    migrated = migrate_level(lvl)
    assert "enemies" not in migrated
    assert migrated["name"] == "L"


# --------------------------------------------------------------------------
# validate_enemy
# --------------------------------------------------------------------------
def test_validate_enemy_ok_for_migrated():
    enemy = migrate_enemy({"x": 1, "y": 2, "left": 0, "right": 100, "behavior": "walker"})
    assert validate_enemy(enemy) == []


def test_validate_enemy_missing_required_keys():
    errors = validate_enemy({"behavior": "walker"})
    # x, y, left, right, type — обязательные
    assert any("x" in e for e in errors)
    assert any("y" in e for e in errors)
    assert any("left" in e for e in errors)
    assert any("right" in e for e in errors)
    assert any("type" in e for e in errors)


def test_validate_enemy_unknown_behavior():
    enemy = {"x": 1, "y": 2, "left": 0, "right": 100, "type": "enemy", "behavior": "teleporter"}
    errors = validate_enemy(enemy)
    assert any("behavior" in e for e in errors)


def test_validate_enemy_invalid_size():
    enemy = {"x": 1, "y": 2, "left": 0, "right": 100, "type": "enemy",
             "behavior": "walker", "w": -5, "h": "big"}
    errors = validate_enemy(enemy)
    assert any("'w'" in e for e in errors)
    assert any("'h'" in e for e in errors)


def test_validate_enemy_rejects_non_dict():
    errors = validate_enemy([1, 2, 3])
    assert errors  # не пустой список ошибок


# --------------------------------------------------------------------------
# validate_level
# --------------------------------------------------------------------------
def test_validate_level_collects_enemy_errors():
    lvl = {
        "name": "L",
        "player_spawn": {"x": 0, "y": 0},
        "platforms": [],
        "flag": {"x": 0, "y": 0},
        "enemies": [
            {"x": 1, "y": 2, "left": 0, "right": 100, "type": "enemy", "behavior": "badRobot"}
        ],
    }
    errors = validate_level(lvl)
    assert any("enemies[0]" in e for e in errors)


def test_validate_level_missing_base_keys():
    errors = validate_level({"enemies": []})
    assert any("player_spawn" in e for e in errors)
    assert any("platforms" in e for e in errors)
    assert any("flag" in e for e in errors)


def test_validate_level_ok_after_migration():
    raw = {"name": "L", "player_spawn": {"x": 0, "y": 0}, "platforms": [],
           "flag": {"x": 0, "y": 0},
           "enemies": [{"x": 1, "y": 2, "left": 0, "right": 100}]}
    migrated = migrate_level(raw)
    assert validate_level(migrated) == []