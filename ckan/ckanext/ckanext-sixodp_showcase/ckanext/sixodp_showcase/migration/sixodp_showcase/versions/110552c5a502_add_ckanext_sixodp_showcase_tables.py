"""Add ckanext-sixodp_showcase tables

Revision ID: 110552c5a502
Revises: e86f64c8f4c4
Create Date: 2026-01-08 10:54:30.159859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '110552c5a502'
down_revision = 'e86f64c8f4c4'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if "showcase_apiset_association" not in tables:
        op.create_table(
            "showcase_apiset_association",
            sa.Column(
                "package_id",
                sa.UnicodeText,
                sa.ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "showcase_id",
                sa.UnicodeText,
                sa.ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )


def downgrade():
    op.drop_table("showcase_apiset_association")
