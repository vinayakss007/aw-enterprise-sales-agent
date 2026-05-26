# Enterprise Sales Agent

AI-powered B2B sales prospecting platform with multi-tenant isolation, a
LangGraph-style sales agent, pluggable CRM and email integrations, and a
campaign execution worker that walks leads through scheduled outreach.

> **Status:** under active development. The agent runs end-to-end with the
> built-in `FakeLLM` (no API key required) and a console email sender. Real
> OpenAI / HubSpot / SMTP integrations are wired but require credentials.

## Quick start

### 1. Local Postgres + run the API

```bash
# Start Postgres + Redis (and optionally the backend container)
docker compose up -d db redis

# Install Python deps
pip install -r requirements-dev.txt

# Apply migrations and start the API
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/enterprise_sales_agent
alembic upgrade head
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000` — health probe at
`http://localhost:8000/api/v1/health`. Interactive docs are at `/docs` when
`DEBUG=true`.

### 2. Run the campaign worker

```bash
# One-off tick (useful in dev / tests)
python -m app.workers campaigns --once

# Long-running loop (one tick every 30 seconds)
python -m app.workers campaigns --interval 30
```

You can also force a tick from an authenticated admin session:

```bash
curl -X POST http://localhost:8000/api/v1/admin/campaigns/tick \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves the SPA at `http://localhost:5173` (proxying API calls to
`localhost:8000`).

## Repository layout

```
app/
├── agents/sales_agent/   # Research → enrich → draft → verify pipeline
│   ├── llm.py            # FakeLLM (default) + OpenAILLM provider
│   ├── nodes.py          # Async node functions, structured trajectory
│   └── graph.py          # SalesAgent orchestrator
├── api/v1/               # FastAPI routes (auth, customer, admin)
├── core/                 # Settings (pydantic-settings v2)
├── db/                   # SQLAlchemy models (multi-tenant)
├── integrations/
│   ├── crm/              # CRMAdapter protocol, Mock + HubSpot adapters
│   └── email/            # EmailSender protocol, Console + SMTP senders
├── observability/        # Logging, Prometheus metrics, optional OTel tracing
├── schemas/              # Pydantic request/response models
├── services/             # Business logic, used by endpoints
└── workers/
    └── campaigns.py      # CampaignWorker — drives campaign assignments

alembic/                  # Schema migrations (0001_initial = baseline)
frontend/                 # React 18 + Vite + Tailwind
infra/docker/             # Dockerfile.backend, prometheus.yml
tests/
├── unit/                 # No-DB tests (run anywhere)
└── integration/          # Need TEST_DATABASE_URL=postgresql+psycopg://...
```

## Configuration

All configuration is environment-driven. Copy and edit:

```bash
cp .env.example .env  # if a template exists; otherwise create one
```

The most important variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/sales_agent` | Postgres connection string |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key — **must change in prod** |
| `LLM_PROVIDER` | `fake` | `fake` (offline) or `openai` |
| `OPENAI_API_KEY` | _empty_ | Required when `LLM_PROVIDER=openai` |
| `EMAIL_PROVIDER` | `console` | `console` (logs only) or `smtp` |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | _empty_ | Required when `EMAIL_PROVIDER=smtp` |
| `DEFAULT_CRM_PROVIDER` | `mock` | Override per-tenant via `Tenant.config['crm']` |
| `DEBUG` | `false` | Enables `/docs`, `create_all` on startup |
| `TRACING_ENABLED` | `false` | Enables OpenTelemetry instrumentation |

CRM credentials are stored per-tenant in `Tenant.config['crm']`:

```json
{
  "crm": {
    "provider": "hubspot",
    "credentials": {"access_token": "<HubSpot private app token>"}
  }
}
```

## Common tasks

```bash
make install           # Install backend + frontend dependencies
make dev               # Run uvicorn with reload
make test              # pytest tests/
make migrate           # alembic upgrade head
make migrate-create m="add x"  # autogenerate a migration
make lint              # ruff check
make format            # ruff format + ruff --fix
make security-check    # bandit + safety
```

## Tests

Unit tests do not need infrastructure:

```bash
pytest tests/unit
```

Integration tests need Postgres reachable via `TEST_DATABASE_URL`:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/test_db
pytest tests/integration
```

CI runs both against a `postgres:16-alpine` service.

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — high-level system design
- [`API.md`](API.md) — REST endpoint reference
- [`SETUP.md`](SETUP.md) — local dev setup walkthrough
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — production deployment guidance
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — common issues
