"""API v1 router - aggregates all endpoint routers."""
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.customer.leads import router as leads_router
from app.api.v1.endpoints.customer.agent import router as agent_router
from app.api.v1.endpoints.customer.campaigns import router as campaigns_router
from app.api.v1.endpoints.customer.crm import router as crm_router
from app.api.v1.endpoints.admin.tenants import router as tenants_router
from app.api.v1.endpoints.admin.users import router as users_router
from app.api.v1.endpoints.admin.usage import router as usage_router

api_router = APIRouter()

# Auth
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Customer endpoints
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(crm_router, prefix="/crm", tags=["crm"])

# Admin endpoints
api_router.include_router(tenants_router, prefix="/admin/tenants", tags=["admin-tenants"])
api_router.include_router(users_router, prefix="/admin/users", tags=["admin-users"])
api_router.include_router(usage_router, prefix="/admin/usage", tags=["admin-usage"])
