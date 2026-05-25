"""initial schema

Brings a fresh Postgres up to the current model state in a single shot. Future
revisions should be generated with ``alembic revision --autogenerate -m ...``
which will diff the live DB against ``app.db.base.Base.metadata``.

Revision ID: 0001
Revises:
Create Date: 2026-05-25
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import inside upgrade() so the module loads cleanly even if models change
    # in later revisions; this baseline always reflects the metadata at the
    # time it was first applied.
    from app.db import models  # noqa: F401  (registers mappers)
    from app.db.base import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db import models  # noqa: F401
    from app.db.base import Base

    Base.metadata.drop_all(bind=op.get_bind())
