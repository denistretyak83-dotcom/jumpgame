.PHONY: setup test lint format coverage clean

PYTHON ?= python

## Setup: создать venv и поставить dev-зависимости
setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install -r requirements-dev.txt

## Test: запустить tests с coverage и порогом покрытия (немедленно при падении -e)
test:
	$(PYTHON) -m pytest -q

## Coverage: запуск pytest с отчётом coverage
coverage:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=html

## Lint: проверить ruff
lint:
	ruffle check .
	ruff format --check .

## Format: отформатировать код ruff (только при осознанном решении)
format:
	ruff format .

## Clean: убрать кеши и артефакты
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist *.egg-info *.spec

