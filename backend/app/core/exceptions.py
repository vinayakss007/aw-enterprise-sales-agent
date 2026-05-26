"""Custom application exceptions."""


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LeadNotFoundException(AppException):
    def __init__(self, lead_id: str):
        super().__init__(f"Lead {lead_id} not found", status_code=404)


class CampaignNotFoundException(AppException):
    def __init__(self, campaign_id: str):
        super().__init__(f"Campaign {campaign_id} not found", status_code=404)


class TenantNotFoundException(AppException):
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant {tenant_id} not found", status_code=404)


class CRMIntegrationError(AppException):
    def __init__(self, message: str):
        super().__init__(f"CRM integration error: {message}", status_code=502)


class RateLimitExceeded(AppException):
    def __init__(self):
        super().__init__("Rate limit exceeded", status_code=429)
