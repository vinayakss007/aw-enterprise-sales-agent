from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.db.models.tenant import Tenant
from app.db.models.usage_metrics import UsageMetrics
from app.schemas.usage import TenantUsageResponse, UsageMetricsResponse


class UsageService:
    def __init__(self, db: Session):
        self.db = db

    async def get_system_metrics(
        self, 
        start_date: str | None = None, 
        end_date: str | None = None, 
        granularity: str = "day"
    ) -> UsageMetricsResponse:
        """
        Get system-wide usage metrics
        """
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=30)
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()

        # Query for system metrics
        query = self.db.query(
            func.date_trunc(granularity, UsageMetrics.timestamp).label('date'),
            func.sum(UsageMetrics.value).label('total_value'),
            func.count(func.distinct(UsageMetrics.tenant_id)).label('active_tenants'),
            func.sum(UsageMetrics.cost_cents).label('total_cost')
        ).filter(
            and_(
                UsageMetrics.timestamp >= start_dt,
                UsageMetrics.timestamp <= end_dt
            )
        ).group_by(
            func.date_trunc(granularity, UsageMetrics.timestamp)
        ).order_by(
            func.date_trunc(granularity, UsageMetrics.timestamp)
        )

        results = query.all()
        
        return UsageMetricsResponse(
            date_range=(start_dt, end_dt),
            granularity=granularity,
            metrics=[{
                'date': result.date.isoformat(),
                'value': result.total_value or 0,
                'active_tenants': result.active_tenants or 0,
                'cost': (result.total_cost or 0) / 100.0  # Convert cents to dollars
            } for result in results],
            totals=self._get_totals(start_dt, end_dt)
        )

    async def get_tenant_usage(
        self, 
        start_date: str | None, 
        end_date: str | None, 
        limit: int, 
        offset: int, 
        sort_by: str, 
        sort_order: str
    ) -> list[TenantUsageResponse]:
        """
        Get tenant usage with pagination
        """
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=30)
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()

        # Query tenant usage with aggregation
        query = self.db.query(
            Tenant.id,
            Tenant.name,
            func.sum(UsageMetrics.value).label('total_usage'),
            func.sum(UsageMetrics.cost_cents).label('total_cost'),
            func.count(func.distinct(UsageMetrics.user_id)).label('active_users'),
            func.count(UsageMetrics.id).label('task_count')
        ).join(
            UsageMetrics, Tenant.id == UsageMetrics.tenant_id
        ).filter(
            and_(
                UsageMetrics.timestamp >= start_dt,
                UsageMetrics.timestamp <= end_dt
            )
        ).group_by(
            Tenant.id, Tenant.name
        )

        # Apply sorting
        def _direction(col):
            return col.desc() if sort_order == "desc" else col.asc()

        if sort_by == "usage":
            query = query.order_by(_direction(func.sum(UsageMetrics.value)))
        elif sort_by == "cost":
            query = query.order_by(_direction(func.sum(UsageMetrics.cost_cents)))
        elif sort_by == "users":
            query = query.order_by(_direction(func.count(func.distinct(UsageMetrics.user_id))))
        else:  # tasks
            query = query.order_by(_direction(func.count(UsageMetrics.id)))

        # Apply pagination
        results = query.offset(offset).limit(limit).all()
        
        return [
            TenantUsageResponse(
                tenant_id=result.id,
                tenant_name=result.name,
                total_usage=result.total_usage or 0,
                total_cost=(result.total_cost or 0) / 100.0,
                active_users=result.active_users or 0,
                task_count=result.task_count or 0
            ) for result in results
        ]

    def _get_totals(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """
        Get aggregated totals for the date range
        """
        from sqlalchemy import func
        totals_query = self.db.query(
            func.sum(UsageMetrics.value).label('total_usage'),
            func.sum(UsageMetrics.cost_cents).label('total_cost'),
            func.count(func.distinct(UsageMetrics.tenant_id)).label('total_tenants'),
            func.count(func.distinct(UsageMetrics.user_id)).label('total_users'),
            func.count(UsageMetrics.id).label('total_tasks')
        ).filter(
            and_(
                UsageMetrics.timestamp >= start_date,
                UsageMetrics.timestamp <= end_date
            )
        )

        result = totals_query.first()
        return {
            'total_usage': result.total_usage or 0,
            'total_cost': (result.total_cost or 0) / 100.0,
            'total_tenants': result.total_tenants or 0,
            'total_users': result.total_users or 0,
            'total_tasks': result.total_tasks or 0
        }
        
    async def export_report(
        self, 
        start_date: str, 
        end_date: str, 
        report_type: str = "csv"
    ) -> dict[str, Any]:
        """
        Export usage report in specified format
        """
        # This would implement the export logic
        # For now, return a mock response
        return {
            "filename": f"usage_report_{start_date}_{end_date}.{report_type}",
            "download_url": f"/api/v1/admin/usage/export/download/{report_type}?start={start_date}&end={end_date}",
            "size": 102400,  # 100KB
            "created_at": datetime.utcnow()
        }