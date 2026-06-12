.PHONY: all format lint test help

all: help

install:
	uv sync --all-packages --group dev

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format . --diff

test:
	uv run pytest $(TEST)

help:
	@echo "format - run code formatters"
	@echo "lint   - run linters"
	@echo "test   - run unit tests"
