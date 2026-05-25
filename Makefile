# Enterprise Sales Agent — developer commands.
# All backend code lives at the repo root under app/. There is no longer a
# separate backend/ subtree.

.PHONY: help install backend-install frontend-install \
        dev backend-dev frontend-dev \
        test backend-test frontend-test \
        migrate migrate-create \
        docker-up docker-down clean-db \
        format lint security-check

help:
	@echo "Enterprise Sales Agent - Development Commands"
	@echo ""
	@echo "  make install            Install backend + frontend dependencies"
	@echo "  make dev                Start backend dev server"
	@echo "  make test               Run backend + frontend tests"
	@echo "  make migrate            Apply Alembic migrations"
	@echo "  make migrate-create m=  Generate a new migration"
	@echo "  make docker-up          Start docker-compose services"
	@echo "  make docker-down        Stop docker-compose services"
	@echo "  make format             Format backend + frontend"
	@echo "  make lint               Lint backend + frontend"
	@echo "  make security-check     Run bandit + safety"

install: backend-install frontend-install

backend-install:
	pip install -r requirements.txt

frontend-install:
	cd frontend && npm install

dev: backend-dev

backend-dev:
	uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

test: backend-test

backend-test:
	pytest tests/ -v

frontend-test:
	cd frontend && npm run test --if-present

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(m)"

docker-up:
	cd infra/docker && docker-compose up -d

docker-down:
	cd infra/docker && docker-compose down

clean-db:
	cd infra/docker && docker-compose down -v
	docker volume prune -f

format:
	ruff format app tests
	ruff check --fix app tests
	cd frontend && npm run format --if-present

lint:
	ruff check app tests
	cd frontend && npm run lint

security-check:
	bandit -r app -ll
	safety check -r requirements.txt
