"""Audit log service.

The service is both a reader (filtered queries, summaries) and a writer
(``record``). Writes form a per-tenant hash chain so any subsequent edit or
deletion is detectable: each row's ``current_hash`` is the SHA-256 of the
previous row's ``current_hash`` concatenated with a canonical JSON encoding
of the new row's fields. The first row in a tenant chain has
``previous_hash = ''``.

Concurrency: ``record`` takes a ``SELECT ... FOR UPDATE`` on the most recent
audit row for the tenant before computing the new hash, so two simultaneous
writes serialise. For very write-heavy tenants this is the obvious next
bottleneck and would benefit from a per-tenant advisory lock; see TODO.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse

logger = logging.getLogger(__name__)


def _canonical_json(value: Any) -> bytes:
    """Stable JSON encoding used as input to the chain hash."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def compute_hash(previous_hash: str | None, record: dict[str, Any]) -> str:
    """Public so verification + tests can recompute hashes externally."""
    h = hashlib.sha256()
    h.update((previous_hash or "").encode("utf-8"))
    h.update(_canonical_json(record))
    return h.hexdigest()


class AuditService:
    """Read + write helpers for the ``audit_log`` table."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def record(
        self,
        *,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str | None = None,
        changes_before: dict[str, Any] | None = None,
        changes_after: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        commit: bool = True,
    ) -> AuditLog | None:
        """Append a tamper-resistant entry to the chain for ``tenant_id``.

        Returns the created row, or ``None`` if persistence failed (audit is
        best-effort — we never let a failed write break the action that was
        being audited). Pass ``commit=False`` if the caller manages the
        transaction and wants the audit row to land atomically with their
        action.
        """
        try:
            # Lock + read the previous row for this tenant. The lock blocks
            # other writers in the same tenant chain so two concurrent
            # callers can't compute hashes against the same predecessor.
            # TODO: use a per-tenant advisory lock for hot tenants.
            previous = (
                self.db.query(AuditLog)
                .filter(AuditLog.tenant_id == tenant_id)
                .order_by(AuditLog.id.desc())
                .with_for_update()
                .first()
            )
            previous_hash = previous.current_hash if previous else ""
            timestamp = datetime.utcnow()

            payload = {
                "timestamp": timestamp.isoformat(),
                "tenant_id": str(tenant_id),
                "user_id": str(user_id) if user_id else None,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "changes_before": changes_before,
                "changes_after": changes_after,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
            current_hash = compute_hash(previous_hash, payload)

            entry = AuditLog(
                timestamp=timestamp,
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                changes_before=changes_before,
                changes_after=changes_after,
                ip_address=ip_address,
                user_agent=user_agent,
                previous_hash=previous_hash,
                current_hash=current_hash,
            )
            self.db.add(entry)
            self.db.flush()
            if commit:
                self.db.commit()
            return entry
        except Exception:  # pragma: no cover — defensive
            logger.exception(
                "audit.record failed: tenant=%s action=%s resource=%s/%s",
                tenant_id,
                action,
                resource_type,
                resource_id,
            )
            try:
                self.db.rollback()
            except Exception:
                pass
            return None

    # ------------------------------------------------------------------ #
    # Verification
    # ------------------------------------------------------------------ #

    def verify_chain(self, tenant_id: str) -> dict[str, Any]:
        """Re-walk the chain and report any tampering.

        Returns a dict with:
          * ``verified`` — True when every link is intact
          * ``count`` — number of rows checked
          * ``broken_at`` — list of audit_log ids whose hashes don't match
        """
        rows: list[AuditLog] = (
            self.db.query(AuditLog)
            .filter(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.id.asc())
            .all()
        )
        broken: list[int] = []
        previous_hash: str | None = ""
        for row in rows:
            payload = {
                "timestamp": row.timestamp.isoformat(),
                "tenant_id": str(row.tenant_id),
                "user_id": str(row.user_id) if row.user_id else None,
                "action": row.action,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "changes_before": row.changes_before,
                "changes_after": row.changes_after,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
            }
            expected = compute_hash(previous_hash, payload)
            if (
                row.previous_hash != previous_hash
                or row.current_hash != expected
            ):
                broken.append(int(row.id))
            previous_hash = row.current_hash
        return {
            "verified": not broken,
            "count": len(rows),
            "broken_at": broken,
        }

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #

    async def get_audit_logs(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLogResponse]:
        """Get audit logs with filtering options."""
        query = self.db.query(AuditLog)

        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(end_date))

        logs = (
            query.order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            AuditLogResponse(
                id=log.id,
                timestamp=log.timestamp,
                tenant_id=str(log.tenant_id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                changes_before=log.changes_before,
                changes_after=log.changes_after,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                previous_hash=log.previous_hash,
                current_hash=log.current_hash,
            )
            for log in logs
        ]

    async def get_audit_summary(
        self,
        tenant_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get audit log summary statistics."""
        query = self.db.query(AuditLog)
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if start_date:
            query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(end_date))

        total_logs = query.count()
        action_counts = dict(
            self.db.query(AuditLog.action, func.count(AuditLog.id))
            .filter(AuditLog.tenant_id == tenant_id if tenant_id else True)
            .group_by(AuditLog.action)
            .all()
        )
        resource_type_counts = dict(
            self.db.query(AuditLog.resource_type, func.count(AuditLog.id))
            .filter(AuditLog.tenant_id == tenant_id if tenant_id else True)
            .group_by(AuditLog.resource_type)
            .all()
        )

        return {
            "total_logs": total_logs,
            "action_counts": action_counts,
            "resource_type_counts": resource_type_counts,
            "date_range": {"start": start_date, "end": end_date},
        }


__all__ = ["AuditService", "compute_hash"]
