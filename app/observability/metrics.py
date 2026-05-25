import time

from prometheus_client import Counter, Histogram, Summary

# Counter metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

agent_executions_total = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_type', 'tenant_id', 'success']
)

token_usage_total = Counter(
    'token_usage_total',
    'Total tokens used',
    ['model', 'operation_type', 'tenant_id']
)

cost_cents_total = Counter(
    'cost_cents_total',
    'Total cost in cents',
    ['tenant_id', 'operation_type']
)

# Histogram metrics (for timing)
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'Duration of API requests',
    ['method', 'endpoint', 'tenant_id']
)

agent_execution_duration = Histogram(
    'agent_execution_duration_seconds',
    'Duration of agent executions',
    ['agent_type', 'tenant_id']
)

agent_step_duration = Summary(
    'agent_step_duration_seconds',
    'Time spent in each agent step',
    ['step_name', 'agent_type', 'tenant_id']
)

def increment_agent_execution(agent_type: str, tenant_id: str, success: bool):
    """Increment the agent execution counter"""
    agent_executions_total.labels(
        agent_type=agent_type,
        tenant_id=tenant_id,
        success=str(success)
    ).inc()

def record_token_usage(model: str, operation_type: str, tenant_id: str, tokens: int):
    """Record token usage"""
    token_usage_total.labels(
        model=model,
        operation_type=operation_type,
        tenant_id=tenant_id
    ).inc(tokens)

def record_cost(tenant_id: str, operation_type: str, cost_cents: int):
    """Record cost in cents"""
    cost_cents_total.labels(
        tenant_id=tenant_id,
        operation_type=operation_type
    ).inc(cost_cents)

def start_timer() -> float:
    """Start a timer"""
    return time.time()

def record_timer_duration(timer_start: float, histogram, labels: dict[str, str] = None):
    """Record duration of an operation"""
    duration = time.time() - timer_start
    if labels:
        histogram.labels(**labels).observe(duration)
    else:
        histogram.observe(duration)