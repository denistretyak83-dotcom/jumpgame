# README — Инструкция разработчика (Phase 1)

Проект: **Jump & Reach the Flag** (2D-платформер, Python + Pygame, Python ≥ 3.11).
Это dev-инструкция: как локально ставить зависимости, запускать тесты/линтер/покрытие,
как это делает CI, как работает headless-режим pygame и как собрать релиз.

---

## 1. Установка dev-окружения

```bash
# 1) Создать venv и активировать
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scriptsctivate

# 2) Поставить зависимости (runtime + dev)
pip install -r requirements-dev.txt
```

`requirements-dev.txt` включает runtime (`requirements.txt` → `pygame`) и инструменты:
`pytest`, `pytest-cov`, `ruff`, `coverage`, `pyinstaller` (для релиза).

Можно также через Makefile: `make setup`.

## 2. Запуск тестов

```bash
pytest -q                 # быстрый прогон
pytest --cov              # тесты + покрытие
make test                 # то же
```

Конфигурация pytest — в `pyproject.toml [tool.pytest.ini_options]`:
- `testpaths = ["tests"]`
- `pythonpath = ["."]` — чтобы `import core`, `models` и пр. работали без установки пакета.

## 3. Линтер и форматтер (ruff)

```bash
ruff check .              # автопроверка (E,F,W,B,I,UP,SIM)
ruff format --check .     # проверка форматирования
ruff format .             # применить форматирование (осознанно!)
make lint                 # check + format --check
```

Конфиг ruф — в `pyproject.toml [tool.ruff]`: line-length 100, target py311,
exclude tests/venv и друго. Тесты свободнее (`per-file-ignores`).

> ⚠️ На проект уже внесены мелкие правки импортов (убраны неиспользуемые
> `SpriteCache`/`ModelVisualData`/`sys`/`List`), чтобы `ruff check .` был чище.
> Если ruff жалуется на оставшийся старый код — это отдельная задача (не форматировать
> весь проект в рамках этой фазы), можно добавить исключения или почистить поэтапно.

## 4. Покрытие тестами

```bash
coverage run -m pytest      # или: pytest --cov
coverage report             # текстовый отчёт, порог fail_under из pyproject (80%)
coverage html               # htmlcov/index.html для просмотра
make coverage
```

Порог покрытия **≥80%** задан в `pyproject.toml [tool.coverage.report] fail_under = 80`.
В CI при падении ниже порога job упадёт.

## 5. Headless-режим pygame (CI без дисплея)

pygame нужен дисплей. Для CI используем dummy-драйверы SDL. Два способа:

1. **env-переменные** (задаются в CI-пайплайне и можно локально):
   ```bash
   export SDL_VIDEODRIVER=dummy
   export SDL_AUDIODRIVER=dummy
   ```
2. **conftest.py** (`tests/conftest.py`): autouse-session-fixture `_headless_pygame`
   ставит эти env **до** импорта pygame и вызывает `pygame.init()`/`pygame.quit()`
   на всю сессию. Поэтому достаточно просто запустить `pytest` — headless сам настроится.

Тесты, которым нужен pygame (например `tests/test_entity.py`, `tests/test_factory.py`),
работают благодаря этому. В CI Ubuntu **xvfb не нужен** при dummy-драйвере.

## 6. CI

`.github/workflows/ci.yml`:
- триггер: push/PR на ветки `main` и `develop`;
- **job `tests`**: checkout@v4 → setup-python@v5 (3.11) → install
  (`requirements-dev.txt`) → `pytest --cov` (coverage в CI) → artifact + порог ≥80%;
  env `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`;
- **job `lint`**: `ruff check .` и `ruff format --check .`.

`.github/workflows/release.yml`:
- триггер: push тега `v*`;
- **job `build`**: собирает one-file exe через PyInstaller
  (`pyinstaller --onefile --noconfirm --name JumpAndReachTheFlag main.py`),
  проверяет `dist/`, выкладывает артефакт;
- **job `release`**: `needs: build`, создаёт GitHub Release через
  `softprops/action-gh-release@v2` и прикрепляет бинарник.

## 7. Сборка релиза (локально, без CI)

```bash
pip install pyinstaller
pyinstaller --onefile --noconfirm --name JumpAndReachTheFlag main.py
# результат: dist/JumpAndReachTheFlag (или .exe на Windows)
```

CI делает то же самое автоматом при пуше тега `v*`.

## 8. Полезное

- Структура: `core/` (Game, EventBus, конфиг, логгер), `models/` (модели, фабрика,
  коллизии), `views/` (рендер/спрайты), `controllers/`, `levels/`, `audio/`, `main.py`.
- Архитектура MVC + EventBus + Data-Driven JSON + DI (без глобалов).
- Игра запускается: `python main.py`.
