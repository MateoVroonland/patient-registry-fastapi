.PHONY: help prod dev install test clean create-migration deploy-migrations rollback-migrations lint test-cov

help:
	@echo "Commands:"
	@echo "  make api      - Run API with hot reload"
	@echo "  make prod     - Production environment (API + DB, applies migrations on API startup)"
	@echo "  make dev      - Only DB for development"
	@echo "  make create-migration message='description' - Create migration"
	@echo "  make deploy-migrations - Deploy migrations"
	@echo "  make rollback-migrations - Rollback last migration"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean environments"
	@echo "  make lint     - Run linting"
	@echo "  make test-cov - Run tests with coverage"

api:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

prod:
	docker compose up -d --build

logs:
	docker compose logs -f

dev:
	docker compose -f docker-compose-dev.yml up -d

install:
	uv sync --frozen --no-install-project

test:
	uv run pytest

clean:
	docker compose down -v --remove-orphans || true
	docker compose -f docker-compose-dev.yml down -v --remove-orphans || true

create-migration:
	@if [ -z "$(message)" ]; then \
		echo "Error: message parameter is required. Usage: make create-migration message='your message'"; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(message)"

deploy-migrations:
	uv run alembic upgrade head

rollback-migrations:
	uv run alembic downgrade -1

test-cov:
	uv run pytest --cov=app --cov-report=term-missing --cov-report=html

lint:
	@echo "Running Ruff..."
	ruff check .
	@echo "Checking formatting..."
	ruff format --check .
	@echo "Running Type Check..."
	ty check .
