.PHONY: help install dev test lint format clean run docker-build docker-up docker-down ingest

help:
	@echo "Available targets:"
	@echo "  install       Install production dependencies"
	@echo "  dev           Install dev dependencies + pre-commit hooks"
	@echo "  run           Run FastAPI server with reload"
	@echo "  test          Run pytest with coverage"
	@echo "  lint          Run flake8 + mypy"
	@echo "  format        Run black + isort"
	@echo "  clean         Remove caches and build artifacts"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start docker-compose services"
	@echo "  docker-down   Stop docker-compose services"
	@echo "  ingest DIR=.. Ingest a directory"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

dev: install
	pre-commit install || true

run:
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -v --cov=src --cov-report=term-missing --cov-report=html tests/

lint:
	flake8 src tests
	mypy src

format:
	isort src tests scripts
	black src tests scripts

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov build dist *.egg-info

docker-build:
	docker build -t rag-pipeline:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

ingest:
	python -m scripts.ingest --directory $(DIR)
