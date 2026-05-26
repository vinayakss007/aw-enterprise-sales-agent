"""End-to-end enrichment + CSV tests against Postgres."""
from __future__ import annotations

import io


def _register_and_login(client, email: str = "alice@enrich.test") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Alice", "password": "hunter22"},
    )
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "hunter22"},
    )
    return resp.json()["access_token"]


def test_enrich_lead_uses_fake_provider_by_default(client):
    token = _register_and_login(client, "enrich1@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/api/v1/customer/leads/",
        json={"email": "lead@target.test", "domain": "target.test"},
        headers=headers,
    )
    assert create.status_code == 200, create.text
    lead_id = create.json()["id"]

    enrich = client.post(
        f"/api/v1/customer/leads/{lead_id}/enrich",
        headers=headers,
    )
    assert enrich.status_code == 200, enrich.text
    body = enrich.json()
    assert body["enriched_data"] is not None
    assert body["enriched_data"]["provider"] == "fake"
    assert body["enriched_data"]["industry"]
    assert body["enriched_data"]["confidence"] == 0.4
    # Headline fields backfilled onto the Lead row.
    assert body["company"]


def test_enrich_lead_404_for_unknown_id(client):
    token = _register_and_login(client, "enrich2@target.test")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/v1/customer/leads/00000000-0000-0000-0000-000000000000/enrich",
        headers=headers,
    )
    assert resp.status_code == 404


def test_enrich_writes_audit_row(client, db_session):
    from app.db.models.audit_log import AuditLog
    from app.db.models.user import User

    token = _register_and_login(client, "enrich3@target.test")
    headers = {"Authorization": f"Bearer {token}"}
    create = client.post(
        "/api/v1/customer/leads/",
        json={"email": "lead@target.test", "domain": "target.test"},
        headers=headers,
    )
    lead_id = create.json()["id"]
    client.post(
        f"/api/v1/customer/leads/{lead_id}/enrich",
        headers=headers,
    )

    user = db_session.query(User).filter(User.email == "enrich3@target.test").one()
    actions = [
        r.action
        for r in db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == user.tenant_id)
        .all()
    ]
    assert "lead.enrich" in actions


def test_csv_roundtrip_export_then_import(client):
    """Create two leads, export, wipe, import the same CSV, count matches."""
    token = _register_and_login(client, "csv@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    a = client.post(
        "/api/v1/customer/leads/",
        json={"email": "a@target.test", "name": "A", "company": "ACo"},
        headers=headers,
    )
    b = client.post(
        "/api/v1/customer/leads/",
        json={"email": "b@target.test", "name": "B", "company": "BCo"},
        headers=headers,
    )
    assert a.status_code == 200 and b.status_code == 200

    export = client.get("/api/v1/customer/leads/export.csv", headers=headers)
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    body = export.text
    assert "a@target.test" in body
    assert "b@target.test" in body

    # Re-import the same CSV; both should be marked as updates because the
    # emails already exist for this tenant.
    csv_bytes = body.encode("utf-8")
    files = {"file": ("leads.csv", io.BytesIO(csv_bytes), "text/csv")}
    upload = client.post(
        "/api/v1/customer/leads/import", files=files, headers=headers
    )
    assert upload.status_code == 200, upload.text
    report = upload.json()
    assert report["updated"] == 2
    assert report["created"] == 0
    assert report["errors"] == []


def test_csv_import_creates_new_rows_and_skips_blanks(client):
    token = _register_and_login(client, "csv2@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    csv_text = (
        "email,name,company\n"
        "new1@target.test,New One,NewCo\n"
        ",,\n"  # blank row -> skipped
        "new2@target.test,New Two,Corp2\n"
    )
    files = {"file": ("leads.csv", io.BytesIO(csv_text.encode()), "text/csv")}
    resp = client.post(
        "/api/v1/customer/leads/import", files=files, headers=headers
    )
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["created"] == 2
    assert report["skipped"] == 1
    assert report["updated"] == 0


def test_csv_import_rejects_non_csv_filename(client):
    token = _register_and_login(client, "csv3@target.test")
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("leads.txt", io.BytesIO(b"email\nfoo@bar.test\n"), "text/plain")}
    resp = client.post(
        "/api/v1/customer/leads/import", files=files, headers=headers
    )
    assert resp.status_code == 400
    assert "csv" in resp.json()["detail"].lower()


def test_csv_export_writes_audit_row_for_import_only(client, db_session):
    """Exports are read-only and don't audit; imports do."""
    from app.db.models.audit_log import AuditLog
    from app.db.models.user import User

    token = _register_and_login(client, "csv4@target.test")
    headers = {"Authorization": f"Bearer {token}"}

    client.get("/api/v1/customer/leads/export.csv", headers=headers)
    files = {
        "file": (
            "leads.csv",
            io.BytesIO(b"email,name\nfoo@target.test,Foo\n"),
            "text/csv",
        )
    }
    client.post("/api/v1/customer/leads/import", files=files, headers=headers)

    user = db_session.query(User).filter(User.email == "csv4@target.test").one()
    actions = [
        r.action
        for r in db_session.query(AuditLog)
        .filter(AuditLog.tenant_id == user.tenant_id)
        .all()
    ]
    assert "lead.import" in actions
    # No "lead.export" action was added — CSV download is intentionally
    # not audited (read-only, no PII change).
    assert "lead.export" not in actions
