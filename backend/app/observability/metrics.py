"""Prometheus metrics definitions."""
from prometheus_client import Counter, Histogram, Summary
import time

# Request metrics
api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code", "tenant_id"],
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint", "tenant_id"],
)

# Agent execution metrics
agent_executions_total = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_type", "tenant_id", "success"],
)

agent_execution_duration = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration",
    ["agent_type", "tenant_id"],
)

# Token and cost metrics
token_usage_total = Counter(
    "token_usage_total",
    "Total tokens used",
    ["model", "operation_type", "tenant_id"],
)

cost_cents_total = Counter(
    "cost_cents_total",
    "Total cost in cents",
    ["tenant_id", "operation_type"],
)


def increment_agent_execution(agent_type: str, tenant_id: str, success: bool):
    agent_executions_total.labels(
        agent_type=agent_type, tenant_id=tenant_id, success=str(success)
    ).inc()


def record_token_usage(model: str, operation_type: str, tenant_id: str, tokens: int):
    token_usage_total.labels(
        model=model, operation_type=operation_type, tenant_id=tenant_id
    ).inc(tokens)


def record_cost(tenant_id: str, operation_type: str, cost_cents: int):
    cost_cents_total.labels(
        tenant_id=tenant_id, operation_type=operation_type
    ).inc(cost_cents)
