# Enterprise Sales Agent

Multi-tenant sales automation platform with deterministic agent workflows, CRM integration, and campaign management.

## Architecture

```
backend/           # FastAPI backend (Python 3.11+)
  app/
    agents/        # Deterministic sales agent (research, scoring, email drafting)
    api/v1/        # REST API endpoints (auth, leads, campaigns, agent, admin)
    core/          # Config, security, rate limiting
    db/            # SQLAlchemy models, migrations
    observability/ # Metrics, tracing, logging, health checks
    services/      # Business logic (CRM, campaigns, admin)
  alembic/         # Database migrations
  tests/           # pytest test suite (60 tests)
frontend/          # React 18 + TypeScript + Tailwind
```

## Quick Start

```bash
# 1. Start infrastructure
docker-compose up -d db redis

# 2. Install backend dependencies
cd backend && pip install -r requirements.txt

# 3. Copy environment
cp .env.example .env  # Edit with your values

# 4. Run migrations (or use DEBUG=true for auto-create)
alembic upgrade head

# 5. Start the server
python -m uvicorn app.main:app --reload --port 8000
```

## Key Features

- **Deterministic Sales Agent**: Multi-step workflow (research → enrich → score → draft email) with zero AI dependency on the critical path
- **Multi-tenant Isolation**: All data access is tenant-scoped
- **CRM Integration**: Adapter pattern with HubSpot implementation (Salesforce/Pipedrive extensible)
- **Campaign Management**: Multi-step campaigns with lead assignment and scheduling
- **Rate Limiting**: Per-tenant rate limiting via Redis (falls back to in-memory)
- **Observability**: Prometheus metrics, structured JSON logging, OpenTelemetry tracing (optional)
- **Test Suite**: 60 unit tests covering agent, services, and auth

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/register` | Register |
| GET/POST | `/api/v1/leads/` | List/Create leads |
| POST | `/api/v1/agent/execute/{lead_id}` | Execute sales agent |
| GET | `/api/v1/agent/executions` | Execution history |
| GET/POST | `/api/v1/campaigns/` | List/Create campaigns |
| POST | `/api/v1/crm/sync-lead/{lead_id}` | Sync lead to CRM |
| GET | `/api/v1/health` | Health check |

## Design Decisions

- **No AI on critical paths**: The sales agent uses deterministic algorithms (rule-based scoring, template email drafting, HTTP-based research). Works fully with no AI keys configured.
- **Redis optional**: App functions normally without Redis — just without caching/rate-limiting persistence.
- **OpenTelemetry optional**: Set `ENABLE_OTEL=true` and install OTel packages to activate tracing.
- **SQLite for tests**: Custom JSONB/UUID types that map to SQLite equivalents enable fast local testing without PostgreSQL.
