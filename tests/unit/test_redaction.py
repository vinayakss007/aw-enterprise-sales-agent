"""PII redaction filter unit tests."""
from __future__ import annotations

import logging
from io import StringIO


def test_redact_strips_email_addresses():
    from app.observability.redaction import redact

    out = redact("user alice@example.com signed in from 1.2.3.4")
    assert "alice@example.com" not in out
    assert "[email]" in out


def test_redact_strips_bearer_tokens():
    from app.observability.redaction import redact

    out = redact("Authorization: Bearer eyJabc.def-ghi_jkl")
    assert "eyJabc.def-ghi_jkl" not in out
    assert "Bearer [REDACTED]" in out


def test_redact_strips_password_in_json():
    from app.observability.redaction import redact

    payload = '{"username":"alice","password":"hunter22"}'
    out = redact(payload)
    assert "hunter22" not in out
    assert '"password":"[REDACTED]"' in out


def test_redact_strips_form_password():
    from app.observability.redaction import redact

    out = redact("username=alice&password=hunter22&grant_type=password")
    assert "hunter22" not in out
    assert "password=[REDACTED]" in out


def test_redact_strips_api_key_and_secret_variants():
    from app.observability.redaction import redact

    out = redact(
        '{"api_key":"sk-abc","client_secret":"def","access_token":"ghi"}'
    )
    assert "sk-abc" not in out
    assert "ghi" not in out


def test_redact_leaves_normal_text_unchanged():
    from app.observability.redaction import redact

    text = "agent finished step research in 32ms"
    assert redact(text) == text


def test_redact_handles_empty_and_non_string():
    from app.observability.redaction import redact

    assert redact("") == ""
    assert redact(None) is None  # type: ignore[arg-type]
    assert redact(42) == 42  # type: ignore[arg-type]


def test_filter_redacts_log_record_message():
    from app.observability.redaction import PIIRedactionFilter

    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname="", lineno=0,
        msg="login attempt for alice@example.com", args=None, exc_info=None,
    )
    PIIRedactionFilter().filter(record)
    assert "alice@example.com" not in record.getMessage()


def test_filter_redacts_format_args():
    from app.observability.redaction import PIIRedactionFilter

    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname="", lineno=0,
        msg="user %s with token %s",
        args=("bob@example.com", "Bearer abc.def"),
        exc_info=None,
    )
    PIIRedactionFilter().filter(record)
    rendered = record.getMessage()
    assert "bob@example.com" not in rendered
    assert "abc.def" not in rendered


def test_install_redaction_attaches_to_handler():
    """End-to-end check using a real StringIO handler."""
    from app.observability.redaction import install_redaction

    logger = logging.getLogger("test.redaction.install")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    sink = StringIO()
    handler = logging.StreamHandler(sink)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    install_redaction([logger])
    logger.info("login for alice@example.com with Bearer xyz123")
    handler.flush()
    output = sink.getvalue()

    assert "alice@example.com" not in output
    assert "xyz123" not in output
    assert "[email]" in output
    assert "Bearer [REDACTED]" in output
