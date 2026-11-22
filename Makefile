PYTHON ?= python
IMAGE ?= unn-2026-fatekhov:local

.PHONY: install run test format-check format lint lint-fix typecheck check docker-build

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m echo_bot

test:
	$(PYTHON) -m pytest -q

format-check:
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff format .

lint:
	$(PYTHON) -m ruff check .

lint-fix:
	$(PYTHON) -m ruff check --fix .

typecheck:
	$(PYTHON) -m mypy

check: format-check lint typecheck test

docker-build:
	docker build -t $(IMAGE) .
