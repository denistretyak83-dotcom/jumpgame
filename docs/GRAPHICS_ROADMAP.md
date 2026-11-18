# Архитектурный роадмап графики — платформер 90-х

> Цель: привести JumpGame к визуальному стилю Sonic/Mario/DuckTales
> (ограниченная палитра, плиточные уровни, живые анимации персонажа,
> параллакс-фон) + создать генератор спрайтов (procedural pixel-art).

## 1. Текущее состояние графики (оценка 3-4/10)
- Спрайты: готовые PNG через AssetLoader + хардкод-фигуры (монета, иконка).
- Тайлы: RetroTiles/TileFactory — базовые; автотайлинга нет.
- Фон: RetroBackground — один слой, нет параллакса.
- Анимации: Animation — простой кадровый проигрыватель, нет squash&stretch.

## 2. Целевая картина (эталон 90-х)
- Палитра: до 64 цветов, 4-битные спрайты.
- Уровни: тайловые (16/32px), автотайлинг по соседям.
- Герой: крупный спрайт, 2-4 направления, idle/run/jump/land/squash.
- Враги: палитра-варианты, 1-2 кадра idle.
- Фон: 3 слоя параллакса (небо, горы, ближние объекты).

## 3. Фазы работы

### ФР-1: SpriteSource — контракт источника кадров [DONE]
- views/sprites/sprite_source.py: Protocol SpriteSource (frames/size/supports)
  + PngSpriteSource (обёртка над AssetLoader).
- SpriteCache: реестр источников (register_source/set_default_source), default "png".
- Тест: tests/test_sprite_source.py.

### ФР-2: ProceduralPixelArt — генератор пиксельных спрайтов [DONE]
- views/sprites/procedural.py: гибридный подход (ASCII-карты героя/врагов
  + фигуры монет/тайлов).
- ProceduralSpriteSource реализует SpriteSource; кадры масштабируются под
  хитбокс (config.player/config.enemy).
- Переключение источника в КОМПОЗИТ: settings.game.sprite_source = "png" | "procedural".
- Тест: tests/test_procedural_sprite.py.

### ФР-3 / 3.5: Автотайлинг [DONE]
- views/tiles/autotile.py: AutoTiler + маски соседей (TILE_MASK_*).
- Renderer: _neighbor_mask (вычисление соседей платформы) + _draw_edges
  (обводка рёбер без соседа). Условный автотайлинг платформ.
- Тест: tests/test_tile_edges.py.

### ФР-4: ParallaxBackground [DONE]
- views/backgrounds/: контракт Background (Protocol) + RetroBackground
  (многослойный: небо/горы/облака), цвета из config.colors, OCP-реестр слоёв.
- Renderer использует RetroBackground через контракт.
- Тест: tests/test_parallax.py.

### ФР-5: Squash & stretch — ЖИВЫЕ анимации героя [ТЕКУЩАЯ/СЛЕДУЮЩАЯ]
- Деформация кадра по состоянию (jump -> растяжение по Y, landing -> сжатие).
- В View-слое (CharacterView), НЕ в модели.
- Тест: кадр меняет размер при прыжке/приземлении.

## 3.1 Оценка прогресса графики
- Старт: 3-4/10. После ФР-1..4: ≈ 7-8/10.
- После ФР-5 (squash&stretch): ≈ 8,5-9/10.

## 4. Принципы (не нарушаем ООП/MVC/SOLID)
- SpriteSource — OCP: PNG и генератор регистрируются как источники.
- View не знает, откуда кадр (PNG или procedural) — только получает frame.
- Палитра/тайлсет — data-driven из config, не хардкод.
- Каждая фаза добавляет тесты, база 320 остаётся зелёной.

## 5. Оценка прогресса
- Старт: 3-4/10. После ФР-1 — 5/10, после ФР-2 — 6/10, после ФР-5 — 8-9/10.