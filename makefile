.PHONY: help install dev test lint format docker-up docker-down clean

help:
	@echo "Golem Population Model - Available Commands"
	@echo "==========================================="
	@echo "make install      - Install dependencies with uv"
	@echo "make dev          - Run API + Dashboard locally"
	@echo "make test         - Run unit tests"
	@echo "make lint         - Lint code"
	@echo "make format       - Format code with black"
	@echo "make docker-up    - Start Docker containers"
	@echo "make docker-down  - Stop Docker containers"
	@echo "make clean        - Clean cache and temp files"

install:
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	uv sync --no-dev

dev:
	@echo "Starting API on port 16050..."
	uv run python -m src.api &
	@sleep 2
	@echo "Starting Dashboard on port 8501..."
	uv run streamlit run src/dashboard.py

test:
	uv run pytest tests/ -v --tb=short

lint:
	uv run flake8 src tests --max-line-length=100

format:
	uv run black src tests --line-length=100

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .venv 2>/dev/null || true
	@echo "Cache cleaned!"
