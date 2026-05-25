# Local development setup

This walkthrough gets you from a fresh clone to a running API with a working
database in about five minutes.

## Prerequisites

- Python 3.11
- Node.js 18 + npm (only if you want the frontend)
- Docker + Docker Compose (for the database)
- Git

## 1. Clone and create a virtualenv

```bash
git clone <repo-url>
cd aw-enterprise-sales-agent

python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes everything in `requirements.txt` plus
`pytest`, `ruff`, and `bandit`.

## 2. Start Postgres (+ Redis) via Docker Compose

```bash
docker compose up -d db redis
```

This starts:

- `ankane/pgvector` Postgres on `localhost:5432` (db: `enterprise_sales_agent`,
  user: `postgres`, password: `postgres`)
- Redis on `localhost:6379`

## 3. Configure environment

Create a `.env` file in the project root:

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/enterprise_sales_agent
SECRET_KEY=dev-secret-key-do-not-use-in-prod
DEBUG=true
LLM_PROVIDER=fake          # offline, deterministic — no API key needed
EMAIL_PROVIDER=console     # logs sent emails to stdout

# Optional — only set if you want real LLM / SMTP delivery
# OPENAI_API_KEY=sk-...
# LLM_PROVIDER=openai
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=...
# SMTP_PASSWORD=...
# SMTP_FROM=noreply@example.com
# EMAIL_PROVIDER=smtp
```

Note the `+psycopg` driver suffix — it must match the `psycopg` package
shipped in `requirements.txt` (psycopg3, not psycopg2).

## 4. Apply migrations

```bash
alembic upgrade head
```

This creates the full schema. Future model changes should ship a migration:

```bash
alembic revision --autogenerate -m "describe change"
```

## 5. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Smoke test it:

```bash
curl http://localhost:8000/api/v1/health
# {"status":"healthy","service":"sales-agent-platform",...}
```

Interactive docs: `http://localhost:8000/docs` (only when `DEBUG=true`).

## 6. Run the campaign worker (optional)

The API does not process campaigns by itself — a separate worker walks active
campaign assignments and fires their email steps:

```bash
# One tick and exit (good for testing)
python -m app.workers campaigns --once

# Long-running loop, one tick every 30 seconds
python -m app.workers campaigns --interval 30
```

For dev / one-off use you can also POST as an admin to
`/api/v1/admin/campaigns/tick`, which processes one tick scoped to the
admin's tenant.

## 7. Frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Vite proxies API requests to `http://localhost:8000`.

## 8. Run tests

```bash
# Tests that don't need infrastructure
pytest tests/unit

# Full suite, requires Postgres
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/test_db
pytest tests/
```

## First user

Register through the API or frontend; the first account in a brand-new
tenant becomes the `owner` automatically. Subsequent users register into
the same tenant via invitation flow.

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","name":"You","password":"hunter22"}'
```

## Troubleshooting

See [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md). The most common issues:

- **`ModuleNotFoundError: psycopg2`** — your `DATABASE_URL` is missing the
  `+psycopg` suffix.
- **`OperationalError: could not connect to server`** — `docker compose ps`
  to check Postgres is up; check the port isn't already taken.
- **JWT `invalid token`** — `SECRET_KEY` changed between requests; pin it
  via `.env`.
