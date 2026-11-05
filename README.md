# jumpgame
Python platformer
# Jump & Reach the Flag

A retro-style pygame platformer restructured into an MVC architecture with
JSON-driven configuration and data-driven levels.

## Project Tree
```
jumpgame/
├── main.py                      # thin entry point
├── requirements.txt            # pygame
├── config/
│   └── settings.json           # all constants/config
├── core/
│   ├── config.py               # loads settings.json -> settings singleton
│   ├── game.py                 # Game class (loop + states)
│   ├── state_manager.py         # GameState enum + StateManager
│   ├── camera.py                # ParallaxCamera
│   ├── asset_loader.py          # fonts + sprite frames
│   └── __init__.py
├── models/
│   ├── entity.py  collision.py  player.py  enemy.py  factory.py
│   └── __init__.py
├── controllers/
│   ├── player_controller.py     enemy_controller.py
│   └── __init__.py
├── views/
│   ├── animation.py  tiles.py  background.py  hud.py  renderer.py
│   └── __init__.py
├── levels/
│   ├── level_manager.py  level_1.json
│   └── __init__.py
├── audio/
│   ├── sound_manager.py
│   └── __init__.py
└── assets/
    ├── sprites/
    │   ├── player_idle/{1,2,3}.png
    │   ├── player_run/right/{1,2,3,4}.png
    │   ├── player_run/left/{1,2,3,4}.png
    │   ├── player_jump/{1,2}.png
    │   └── enemy_walk/{1,2,3,4}.png
    ├── sounds/bgm_song.ogg
    └── fonts/PressStart2P-Regular.ttf
```

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Place the asset files (sprite PNG folders, the .ogg music file, and the
   .ttf font) under the `assets/` directory using the exact names shown in
   the tree above: `assets/sprites/player_idle/1.png` ... ,
   `assets/sprites/player_run/right/`, `assets/sprites/player_run/left/`,
   `assets/sprites/player_jump/`, `assets/sprites/enemy_walk/`,
   `assets/sounds/bgm_song.ogg`, `assets/fonts/PressStart2P-Regular.ttf`.

3. Run the game:

```bash
python main.py
```

## Controls

- Move: Left / Right arrow keys (or A / D)
- Jump: Space (or W / Up arrow)
- Quit: Esc
- Restart (after win / game over): R

## Level Data (JSON schema)

Every level lives in `levels/` as a `.json` file with this schema:

```json
{
  "name": "Green Valley",
  "next_level": null,           // set to another level name to chain (or null)
  "player_spawn": {"x": 50, "y": 100},
  "platforms": [ {"x": 0, "y": 540, "w": 200, "h": 30, "style": "grass_top"} ],
  "coins":     [ {"x": 340, "y": 310, "w": 20, "h": 20} ],
  "enemies":   [ {"x": 320, "y": 510, "left": 310, "right": 480} ],
  "flag":      {"x": 700, "y": 300, "w": 30, "h": 60}
}
```

Fields:

- `name`: display name for the level.
- `next_level`: the JSON filename (without `.json`) of the next level, or `null`.
- `player_spawn`: where the player starts, in pixels `{x, y}`.
- `platforms`: array of `{x, y, w, h, style}`. Coordinates are absolute pixels.
  `style` selects the tile renderer (`grass_top` or `floating_platform`).
- `coins`: array of `{x, y, w, h}` coin collision boxes.
- `enemies`: array of `{x, y, left, right}`. `left`/`right` are the patrol
  boundaries the enemy walks between before turning around.
- `flag`: the winning flag collision box `{x, y, w, h}`.

### Adding a new level (level_2.json)

1. Copy `levels/level_1.json` to `levels/level_2.json`.
2. Edit coordinates/objects as desired (all are absolute pixel values for a
   `800x600` screen, but you can also resize via `config/settings.json`).
3. Set `"name": "..."` and `"next_level": null` (or the next level after it).
4. To chain from level 1, set `"next_level": "level_2"` in `level_1.json`.
5. Load it in `core/game.py` by passing `"level_2"` to `load_level(...)`,
   and to the next level set `"next_level"` accordingly. The `LevelManager`
   will resolve the filename automatically (`.json` is appended if missing).
6. Save via `level_manager.save_level(level_dict, "level_2")` if you build it
   programmatically.