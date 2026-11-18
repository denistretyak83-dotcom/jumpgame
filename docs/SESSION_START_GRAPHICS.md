# SESSION_START_GRAPHICS — старт новой сессии (направление «Графика 90-х»)

> Читать ПЕРВЫМ при работе над графикой (Sonic/Mario/DuckTales стиль),
> особенно если контекст предыдущей сессии утерян.

## 1. Контекст проекта
- JumpGame: Python + pygame, MVC/SOLID. Рефакторинг Фаз 1-13 завершён (оценка ~9,5/10).
- Графика: ФР-1..ФР-4 ЗАКРЫТЫ (353 passed). Остаётся ФР-5.

## 2. Что уже есть (арт-пайплайн)
1. **SpriteSource** (views/sprites/sprite_source.py):
   - Protocol: frames(key, count) / size() / supports(key).
   - PngSpriteSource (из AssetLoader), ProceduralSpriteSource (генератор).
2. **ProceduralPixelArt** (views/sprites/procedural.py):
   - ASCII-карты героя/врагов + фигуры монет/тайлов.
   - Кадры масштабируются под хитбокс из config.player/enemy.
   - Переключение: settings.game.sprite_source = "png"|"procedural".
3. **Автотайлинг** (views/tiles/autotile.py + Renderer):
   - AutoTiler, TILE_MASK_*, _neighbor_mask, _draw_edges. Условный тайлинг платформ.
4. **ParallaxBackground** (views/backgrounds/):
   - Контракт Background (Protocol) + RetroBackground (небо/горы/облака).
   - Цвета из config.colors, OCP-реестр слоёв (_layers).

## 3. НЕОТЛОЖНОЕ ЗАДАНИЕ: ФР-5 squash&stretch
- Локация правки: views/character_view.py, метод render().
- По state.anim_key деформировать кадр:
  * jump -> pygame.transform.scale(шире/выше) (stretch по Y).
  * landing/fall -> squash по Y (растянуть по X).
- НЕ трогать модель. Тест: кадр меняет размер при jump/landing.
- Цель: 353 + N passed; mypy 0; ruff чистый.

## 4. Переключение procedural-графики в игре
- config/settings.json -> game.sprite_source = "procedural" (герой/враги из генератора).
- фон: RetroBackground (всегда параллакс). Или "png".

## 5. Проверка
```bash
python -m pytest tests/ -q        # база 353
mypy models core                  # 0 ошибок
ruff check . && ruff format --check .
```
## 6. Принципы (не нарушаем)
Арт-пайплайн только в View-слое; модель НЕ меняется под графику.
OCP: новый источник/слой/тайл подключается регистрацией, без правки логики.
Темы/палитра из config.colors, не хардкод.
Каждый шаг фиксируется коммитом + обновлением этого документа.


---

# Сводка документов

| Документ | Действие |
|---|---|
| `docs/GRAPHICS_ROADMAP.md` | обновить секцию «3. Фазы» (ФР-1..4 done, ФР-5 текущая) |
| `docs/AUDIT_GRAPHICS.md` | заменить (оценка 7-8/10) |
| `docs/SESSION_START.md` | обновить раздел «задачи» (база 353, ФР-5) |
| `docs/SESSION_START_GRAPHICS.md` | **новый** — старт сессии по графике |
