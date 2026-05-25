# Enterprise Sales Agent Platform

An enterprise-grade AI-powered sales agent platform with multi-CRM integration, admin management, and comprehensive observability.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Database Setup](#database-setup)
- [Getting Started](#getting-started)
- [Environment Configuration](#environment-configuration)
- [Development](#development)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Monitoring](#monitoring)
- [Security](#security)

## Features

### Core Agent Capabilities
- Automated lead research and company enrichment
- Personalized outreach email drafting
- Multi-CRM integration (HubSpot, Salesforce, Pipedrive, Zoho, Close, Freshsales)
- Gmail draft integration with approval workflow
- RAG system for product FAQs and objection handling
- Model routing with cost optimization

### Admin Management
- Multi-tenant management
- User role management (Owner, Admin, User, Viewer)
- Usage and billing reporting
- System metrics dashboard
- Tenant configuration management
- Audit logging and compliance

### Customer Management
- Lead management and tracking
- Campaign management
- Communication history
- Sales pipeline management

### Security & Compliance
- SSO integration (Okta, Azure AD, Google Workspace)
- Role-based access control (RBAC)
- Data encryption and PII protection
- SOC 2 compliance features
- Audit trail with tamper resistance

## Architecture

### Tech Stack
- **Backend**: FastAPI, PostgreSQL with pgvector, LangGraph
- **Frontend**: React 18+, TypeScript, Tailwind CSS
- **AI/ML**: OpenAI API, LangChain/LangGraph
- **Infrastructure**: Docker, Kubernetes, Terraform
- **Observability**: Prometheus, Grafana, Jaeger, OpenTelemetry

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Data Store    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL   │
│                 │    │                 │    │   + pgvector)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   AI Agent Core   │
                    │   (LangGraph)     │
                    └───────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐    ┌───────▼────────┐    ┌──────▼──────┐
│  CRM Systems   │    │  OpenAI API    │    │  Caching    │
│ (HubSpot,       │    │                │    │  (Redis)    │
│ Salesforce,     │    │                │    │             │
│ etc.)           │    │                │    │             │
└────────────────┘    └────────────────┘    └─────────────┘
```

## Database Setup

The application requires PostgreSQL with pgvector extension. You can use the provided TimescaleDB connection string:

```
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require
```

### Database Schema Initialization

The application will create all required tables automatically using Alembic migrations. The schema includes:

- User management with tenant isolation
- Lead tracking with enrichment data
- Agent execution history
- Knowledge base with embeddings
- Usage metrics and audit logs
- Campaign management tables

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- OpenAI API key
- TimescaleDB connection string

### Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd enterprise-sales-agent
```

2. Copy environment files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Set required environment variables in `backend/.env`:
```bash
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require
SECRET_KEY=generate_a_strong_secret_key
```

4. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

5. Install frontend dependencies:
```bash
cd ../frontend
npm install
```

6. Start the application:
```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Start frontend (in another terminal)
cd frontend
npm run dev
```

7. The application will be available at:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - Jaeger UI: http://localhost:16686 (if running locally with observability)
   - Prometheus: http://localhost:9090 (if running locally with observability)

## Environment Configuration

### Backend Environment Variables
```bash
# Application
PROJECT_NAME=Enterprise Sales Agent
VERSION=1.0.0
API_V1_STR=/api/v1
DEBUG=true

# Database
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs
OPENAI_API_KEY=your-openai-api-key
SERPAPI_API_KEY=your-serpapi-key
CLEARBIT_API_KEY=your-clearbit-key

# Redis (for caching, optional)
REDIS_URL=redis://localhost:6379/0

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

### Frontend Environment Variables
```bash
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Enterprise Sales Agent
VITE_DEBUG=true
```

## Development

### Backend Development
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Development
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests (if implemented)
cd frontend
npm run test
```

### Database Migrations
```bash
# Navigate to backend
cd backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## Deployment

### Production Deployment

The application can be deployed using:
- Kubernetes with the provided manifests
- Cloud Run with the Docker images
- Traditional VMs with Docker Compose

### CI/CD Pipeline

A GitHub Actions workflow is included for:
- Automated testing
- Security scanning
- Docker image building
- Deployment to staging and production

## API Documentation

The API provides comprehensive documentation at:
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### API Endpoints

#### Authentication
- `POST /api/v1/auth/token` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

#### Admin APIs
- `GET /api/v1/admin/users` - List all users (admin)
- `GET /api/v1/admin/tenants` - List all tenants (admin)
- `GET /api/v1/admin/usage` - Usage metrics (admin)
- `POST /api/v1/admin/crm/config` - Configure CRM (admin)

#### Customer APIs
- `GET /api/v1/customer/leads` - List leads
- `POST /api/v1/customer/leads` - Create lead
- `POST /api/v1/customer/agent/execute/{lead_id}` - Run sales agent
- `GET /api/v1/customer/crm/sync/{lead_id}` - Sync to CRM

## Monitoring

The application includes comprehensive observability:

### Metrics
- API request counts and durations
- Agent execution metrics
- Token usage and costs
- System performance
- Business KPIs

### Tracing
- Distributed tracing across services
- Request flow visualization
- Performance bottleneck identification

### Logging
- Structured JSON logs
- PII redaction
- Contextual information

### Health Checks
- `GET /api/v1/health` - Overall health
- `GET /api/v1/health/ready` - Readiness for requests
- `GET /api/v1/health/live` - Liveness for container orchestration

## Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- SSO integration capability
- Multi-factor authentication support

### Data Protection
- Encryption at rest and in transit
- PII protection and tokenization
- Field-level encryption for sensitive data

### Compliance
- SOC 2 Type I & II ready
- GDPR compliance
- Audit logging with tamper resistance

### Security Best Practices
- Input validation and sanitization
- Rate limiting
- Secure session management
- Regular security updates

## Database Schema

The application uses PostgreSQL with the following key tables:

### User Management
- `users`: Stores user accounts with tenant association and roles
- `tenants`: Manages tenant isolation and configurations

### Lead Management
- `leads`: Tracks prospect information and enrichment data
- `crm_sync_log`: Logs of CRM synchronization events

### Agent Operations
- `agent_executions`: Records of all agent executions with results
- `agent_execution_steps`: Detailed step-by-step execution logs
- `knolwedge_base`: Embeddings for RAG system

### Auditing & Analytics
- `usage_metrics`: Usage tracking for billing and analytics
- `audit_log`: Tamper-resistant audit trail

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, please contact the development team or open an issue in the repository.

## Acknowledgments

- Built with FastAPI, React, and LangGraph
- AI capabilities powered by OpenAI
- CRM integrations for HubSpot, Salesforce, and more
- Observability with Prometheus, Grafana, and Jaeger

---

Made with ❤️ for the sales community.