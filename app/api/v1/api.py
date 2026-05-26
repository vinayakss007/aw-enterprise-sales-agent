from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, customer

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Admin endpoints
api_router.include_router(admin.users.router, prefix="/admin/users", tags=["admin-users"])
api_router.include_router(admin.tenants.router, prefix="/admin/tenants", tags=["admin-tenants"])
api_router.include_router(admin.usage.router, prefix="/admin/usage", tags=["admin-usage"])
api_router.include_router(admin.crm_config.router, prefix="/admin/crm", tags=["admin-crm"])
api_router.include_router(admin.campaigns.router, prefix="/admin/campaigns", tags=["admin-campaigns"])

# Customer endpoints
api_router.include_router(customer.leads.router, prefix="/customer/leads", tags=["customer-leads"])
api_router.include_router(customer.agent.router, prefix="/customer/agent", tags=["customer-agent"])
api_router.include_router(customer.campaigns.router, prefix="/customer/campaigns", tags=["customer-campaigns"])
api_router.include_router(customer.crm.router, prefix="/customer/crm", tags=["customer-crm"])