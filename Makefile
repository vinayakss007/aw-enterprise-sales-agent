# Enterprise Sales Agent

.PHONY: help install dev test lint format db-migrate docker-up docker-down

help:
	@echo "Enterprise Sales Agent"
	@echo ""
	@echo "  make install       Install all dependencies"
	@echo "  make dev           Start backend dev server"
	@echo "  make test          Run backend tests"
	@echo "  make lint          Run linter"
	@echo "  make format        Format code"
	@echo "  make db-migrate    Run Alembic migrations"
	@echo "  make docker-up     Start infra services (postgres, redis)"
	@echo "  make docker-down   Stop infra services"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	cd backend && python -m uvicorn app.main:app --reload --port 8000

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check app/

format:
	cd backend && ruff format app/ tests/

db-migrate:
	cd backend && alembic upgrade head

db-revision:
	cd backend && alembic revision --autogenerate -m "$(msg)"

docker-up:
	docker-compose up -d db redis

docker-down:
	docker-compose down
