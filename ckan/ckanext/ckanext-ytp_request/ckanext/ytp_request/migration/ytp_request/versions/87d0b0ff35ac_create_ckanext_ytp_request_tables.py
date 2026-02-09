"""Create ckanext-ytp_request tables

Revision ID: 87d0b0ff35ac
Revises: 
Create Date: 2026-01-12 08:44:23.990712

"""
import datetime
import uuid

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '87d0b0ff35ac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()

    if "member_request" not in tables:
        op.create_table(
            "member_request",
            sa.Column("id ", sa.UnicodeText, primary_key=True, default=uuid.uuid4),
            sa.Column("membership_id ", sa.UnicodeText, sa.ForeignKey("member.id")),
            sa.Column("request_date ", sa.DateTime, default=datetime.datetime.now),
            sa.Column("role ", sa.UnicodeText),
            sa.Column("handling_date ", sa.DateTime),
            sa.Column("handled_by ", sa.UnicodeText),
            sa.Column("language ", sa.UnicodeText),
            sa.Column("message ", sa.UnicodeText),
            sa.Column("status ", sa.UnicodeText, default="pending"),
        )

def downgrade():
    op.drop_table("member_request")
