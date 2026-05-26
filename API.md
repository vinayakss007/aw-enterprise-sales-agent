# Enterprise Sales Agent - API Documentation

## Base URL
All API endpoints are accessible under `/api/v1/` relative to your server URL.

## Authentication
Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /api/v1/auth/token
Authenticate user and retrieve access token. The endpoint accepts
``application/x-www-form-urlencoded`` (OAuth2 password flow), not JSON.

**Form fields:**
- `username` — user's email
- `password` — user's password

**Response:**
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer"
}
```

#### POST /api/v1/auth/register
Register a new user

**Request:**
```json
{
  "name": "Full Name",
  "email": "user@example.com",
  "password": "user_password"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "Full Name",
  "role": "owner",
  "tenant_id": "uuid",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### GET /api/v1/auth/me
Get current user information

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "Full Name",
  "role": "owner",
  "tenant_id": "uuid",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Customer - Leads

#### GET /api/v1/customer/leads
Get list of leads for current user's tenant

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (integer, default: 0): Number of records to skip
- `limit` (integer, default: 100): Maximum number of records to return

**Response:**
```json
[
  {
    "id": "uuid",
    "tenant_id": "uuid",
    "user_id": "uuid",
    "email": "lead@example.com",
    "name": "Lead Name",
    "company": "Lead Company",
    "domain": "leadcompany.com",
    "title": "Lead Title",
    "linkedin_url": "https://linkedin.com/in/lead",
    "phone": "+1234567890",
    "status": "new",
    "source": "agent",
    "enriched_data": {},
    "crm_contact_id": "crm_contact_id",
    "crm_account_id": "crm_account_id",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

#### POST /api/v1/customer/leads
Create a new lead

**Headers:**
- `Authorization: Bearer <token>`

**Request:**
```json
{
  "email": "lead@example.com",
  "name": "Lead Name",
  "company": "Lead Company",
  "domain": "leadcompany.com",
  "title": "Lead Title",
  "linkedin_url": "https://linkedin.com/in/lead",
  "phone": "+1234567890",
  "source": "agent"
}
```

**Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "email": "lead@example.com",
  "name": "Lead Name",
  "company": "Lead Company",
  "domain": "leadcompany.com",
  "title": "Lead Title",
  "linkedin_url": "https://linkedin.com/in/lead",
  "phone": "+1234567890",
  "status": "new",
  "source": "agent",
  "enriched_data": {},
  "crm_contact_id": "crm_contact_id",
  "crm_account_id": "crm_account_id",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### GET /api/v1/customer/leads/{lead_id}
Get a specific lead

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "email": "lead@example.com",
  "name": "Lead Name",
  "company": "Lead Company",
  "domain": "leadcompany.com",
  "title": "Lead Title",
  "linkedin_url": "https://linkedin.com/in/lead",
  "phone": "+1234567890",
  "status": "new",
  "source": "agent",
  "enriched_data": {},
  "crm_contact_id": "crm_contact_id",
  "crm_account_id": "crm_account_id",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### PUT /api/v1/customer/leads/{lead_id}
Update a specific lead

**Headers:**
- `Authorization: Bearer <token>`

**Request:**
```json
{
  "email": "newemail@example.com",
  "name": "Updated Lead Name",
  "company": "Updated Lead Company",
  "status": "qualified"
}
```

**Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "email": "newemail@example.com",
  "name": "Updated Lead Name",
  "company": "Updated Lead Company",
  "domain": "leadcompany.com",
  "title": "Lead Title",
  "linkedin_url": "https://linkedin.com/in/lead",
  "phone": "+1234567890",
  "status": "qualified",
  "source": "agent",
  "enriched_data": {},
  "crm_contact_id": "crm_contact_id",
  "crm_account_id": "crm_account_id",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### DELETE /api/v1/customer/leads/{lead_id}
Archive a lead (soft delete)

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Lead archived successfully"
}
```

### Customer - Agent

#### POST /api/v1/customer/agent/execute/{lead_id}
Execute an agent on a specific lead

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `agent_type` (string, default: "research"): Type of agent to execute (research, outreach, follow-up)

**Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "lead_id": "uuid",
  "agent_type": "research",
  "trajectory": [],
  "success": true,
  "tokens_input": 1200,
  "tokens_output": 500,
  "cost_cents": 15,
  "started_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:01:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### GET /api/v1/customer/agent/executions
Get agent execution history

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (integer, default: 0): Number of records to skip
- `limit` (integer, default: 50): Maximum number of records to return

**Response:**
```json
{
  "executions": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "user_id": "uuid",
      "lead_id": "uuid",
      "agent_type": "research",
      "trajectory": [],
      "success": true,
      "tokens_input": 1200,
      "tokens_output": 500,
      "cost_cents": 15,
      "started_at": "2023-01-01T00:00:00Z",
      "completed_at": "2023-01-01T00:01:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

#### GET /api/v1/customer/agent/executions/{execution_id}
Get a specific agent execution

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "lead_id": "uuid",
  "agent_type": "research",
  "trajectory": [],
  "success": true,
  "tokens_input": 1200,
  "tokens_output": 500,
  "cost_cents": 15,
  "started_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:01:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Admin Endpoints

#### GET /api/v1/admin/users
Get list of users (admin only)

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "tenant_id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "role": "admin",
    "is_active": true,
    "is_verified": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

#### GET /api/v1/admin/tenants
Get list of tenants (admin only)

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Tenant Name",
    "subdomain": "tenant-subdomain",
    "plan": "pro",
    "status": "active",
    "config": {},
    "limits": {},
    "billing_email": "billing@example.com",
    "is_verified": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

#### GET /api/v1/admin/usage
Get usage metrics (admin only)

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "tenant_id": "uuid",
    "user_id": "uuid",
    "resource_type": "tokens",
    "resource_id": "agent_execution",
    "amount": 1200,
    "unit": "tokens",
    "description": "Tokens used in agent execution",
    "created_at": "2023-01-01T00:00:00Z"
  }
]
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error description"
}
```

## Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error