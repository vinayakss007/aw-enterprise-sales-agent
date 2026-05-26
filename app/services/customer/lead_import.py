"""CSV import / export helpers for leads.

Import accepts the same header set the export emits (so a roundtrip is
lossless). Unknown columns are stored under ``enriched_data["custom"]``
so a one-line spreadsheet round trip doesn't drop anything.

Validation rules:
  * Each row must have at least one of ``email`` / ``name`` / ``company`` —
    a totally blank row is skipped.
  * ``email`` is treated as the natural key; rows with a duplicate email
    in the same tenant update the existing lead instead of creating a
    new one.
  * Bad rows are collected into ``ImportReport.errors`` so the UI can
    display them; the import never raises mid-stream.
"""
from __future__ import annotations

import csv
import io
import logging
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.lead import Lead
from app.db.models.user import User

logger = logging.getLogger(__name__)


CSV_FIELDS: tuple[str, ...] = (
    "email",
    "name",
    "company",
    "domain",
    "title",
    "linkedin_url",
    "phone",
    "status",
    "source",
)
_KNOWN = set(CSV_FIELDS)


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def _normalise(row: dict[str, Any]) -> dict[str, Any]:
    """Lower-case + strip header names, drop blank values."""
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            continue
        normalised_key = str(key).strip().lower()
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        cleaned[normalised_key] = value
    return cleaned


def _is_blank(row: dict[str, Any]) -> bool:
    return not any(row.get(key) for key in ("email", "name", "company"))


def import_leads_csv(
    db: Session,
    user: User,
    *,
    text: str,
) -> ImportReport:
    """Parse ``text`` (a UTF-8 CSV blob) and upsert leads for the user's tenant."""
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return ImportReport(errors=[{"row": 0, "error": "empty CSV"}])

    report = ImportReport()
    seen_emails: set[str] = set()
    for row_index, raw_row in enumerate(reader, start=2):  # row 1 is header
        try:
            row = _normalise(raw_row)
            if _is_blank(row):
                report.skipped += 1
                continue

            extras = {k: v for k, v in row.items() if k not in _KNOWN}

            email = (row.get("email") or "").lower() or None
            if email and email in seen_emails:
                # Same email twice in one upload -> treat as update of itself.
                report.skipped += 1
                continue
            if email:
                seen_emails.add(email)

            existing = (
                db.query(Lead)
                .filter(Lead.tenant_id == user.tenant_id, Lead.email == email)
                .first()
                if email
                else None
            )

            if existing is None:
                lead = Lead(
                    id=uuid.uuid4(),
                    tenant_id=user.tenant_id,
                    user_id=user.id,
                    email=email,
                    name=row.get("name"),
                    company=row.get("company"),
                    domain=row.get("domain"),
                    title=row.get("title"),
                    linkedin_url=row.get("linkedin_url"),
                    phone=row.get("phone"),
                    status=row.get("status") or "new",
                    source=row.get("source") or "import",
                    enriched_data={"custom": extras} if extras else None,
                )
                db.add(lead)
                report.created += 1
            else:
                # Don't blank a populated cell — only fill missing ones.
                for field_name in (
                    "name",
                    "company",
                    "domain",
                    "title",
                    "linkedin_url",
                    "phone",
                ):
                    new_value = row.get(field_name)
                    if new_value and not getattr(existing, field_name):
                        setattr(existing, field_name, new_value)
                if row.get("status"):
                    existing.status = row["status"]
                if extras:
                    enriched = dict(existing.enriched_data or {})
                    custom = dict(enriched.get("custom") or {})
                    custom.update(extras)
                    enriched["custom"] = custom
                    existing.enriched_data = enriched
                existing.updated_at = datetime.utcnow()
                report.updated += 1
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("import row %d failed", row_index)
            report.errors.append({"row": row_index, "error": str(exc)})

    db.commit()
    return report


def export_leads_csv(leads: Iterable[Lead]) -> str:
    """Render leads as a CSV string with the canonical header set."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        writer.writerow(
            {
                "email": lead.email or "",
                "name": lead.name or "",
                "company": lead.company or "",
                "domain": lead.domain or "",
                "title": lead.title or "",
                "linkedin_url": lead.linkedin_url or "",
                "phone": lead.phone or "",
                "status": lead.status or "",
                "source": lead.source or "",
            }
        )
    return buffer.getvalue()


__all__ = [
    "CSV_FIELDS",
    "ImportReport",
    "import_leads_csv",
    "export_leads_csv",
]
