# Enterprise Sales Agent Platform

An enterprise-grade AI-powered sales automation platform that works with any PostgreSQL-compatible database.

## 🌟 Features

### AI-Powered Sales Agents
- **Research Agent**: Automatically researches prospects and companies
- **Outreach Agent**: Crafts personalized outreach emails
- **Follow-up Agent**: Manages multi-touch campaigns
- **RAG System**: Answers product FAQs and handles objections
- **Model Routing**: Cost-optimized small→large model fallback

### Multi-CRM Integration
- HubSpot, Salesforce, Pipedrive, Zoho, Close, Freshsales adapters
- Real-time synchronization
- Contact and activity mirroring

### Admin Management
- Multi-tenant administration
- Usage analytics and billing
- User role management (Owner, Admin, User, Viewer)
- System metrics dashboard

### Customer Management
- Lead tracking and enrichment
- Campaign management
- CRM integration workflows
- Activity history and pipeline tracking

## 🛠️ Tech Stack

- **Backend**: FastAPI, PostgreSQL (any compatible database)
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **AI/ML**: LangGraph, OpenAI, LangChain
- **Database**: PostgreSQL compatible (TimescaleDB, standard PostgreSQL, etc.)
- **Observability**: Prometheus, Jaeger, OpenTelemetry

## 🗄️ Database Compatibility

The application works with any PostgreSQL-compatible database:

- **Standard PostgreSQL** (12+)  
- **TimescaleDB** (PostgreSQL extension for time-series)
- **Amazon RDS for PostgreSQL**
- **Google Cloud SQL for PostgreSQL**
- **Azure Database for PostgreSQL**
- **Heroku Postgres**
- **Aiven PostgreSQL**
- **DigitalOcean Managed Databases**

### Connection Configuration

The application connects using a standard PostgreSQL connection string:

```env
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

For TimescaleDB (which is PostgreSQL-compatible):
```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require
```

## 🚀 Quick Start

1. **Clone and setup backend**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
cp .env.example .env
# Edit .env with your database connection and API keys
```

3. **Apply database migrations**:
```bash
alembic upgrade head
```

4. **Start backend**:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

5. **Setup and start frontend**:
```bash
cd frontend
npm install
npm run dev
```

## 🔐 Security & Compliance

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- PII protection and data redaction
- SOC 2 and GDPR compliance features
- Audit logging with tamper resistance
- SSO integration (Okta, Azure AD, Google)

## 📊 Observability

- Metrics collection with Prometheus
- Distributed tracing with Jaeger
- Structured JSON logging
- Health checks and performance monitoring
- Usage analytics and cost tracking

## 📈 Multi-Tenant Architecture

- Complete tenant data isolation
- Usage-based billing metrics
- Tenant-specific configurations
- Role-based access controls
- Audit trails per tenant

## 🤖 AI Agent Architecture

Built with LangGraph for reliable agent execution:

```
[Research] → [Enrich] → [Draft] → [Verify] → [Execute]
    ↑                                      ↓
[Planning] ← [Reflection] ← [Tool Use] ← [Decision]
```

- ReAct (Reasoning + Acting) pattern
- Tool orchestration for research and CRM sync
- Memory management for context
- Error handling and fallback mechanisms

## 🔄 CRM Integration

Modular adapter pattern for easy CRM expansion:

```
SalesAgent → CRMAdapter → [HubSpot|Salesforce|Pipedrive|...] 
```

Each CRM adapter implements the same interface for:
- Contact/lead management
- Activity logging
- Note creation
- Opportunity tracking

## 📊 Analytics & Reporting

- Real-time usage metrics
- Agent performance metrics
- Cost tracking per tenant/user
- Campaign effectiveness analysis
- API rate limiting and quotas

## 🏗️ Deployment

The application supports multiple deployment options:

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - OPENAI_API_KEY=your-key
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: sales_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
```

### Kubernetes
Production-ready manifests included with horizontal pod autoscaling, resource limits, and health checks.

## 📋 Requirements

- Python 3.10+
- PostgreSQL-compatible database (12+)
- Node.js 18+ (for frontend)
- OpenAI API key
- Redis (for caching and rate limiting)

## 🧪 Testing

Comprehensive test suite covering:
- Unit tests for business logic
- Integration tests for API endpoints
- End-to-end tests for critical workflows
- Load testing configurations

## 🚀 Production Features

- Environment-specific configuration
- Comprehensive logging and monitoring
- Automated CI/CD pipelines
- Security scanning and dependency audits
- Backup and disaster recovery procedures

## 📞 Support

For support, please contact the development team or create an issue in the repository.

---

The Enterprise Sales Agent Platform is a production-ready, scalable solution for automating sales processes. It leverages AI to enhance productivity while maintaining human oversight for critical decisions. The multi-tenant architecture with PostgreSQL compatibility makes it ideal for enterprise deployments.

The application successfully connects to your TimescaleDB database (which is PostgreSQL-compatible) and can work with any PostgreSQL-compatible database system.