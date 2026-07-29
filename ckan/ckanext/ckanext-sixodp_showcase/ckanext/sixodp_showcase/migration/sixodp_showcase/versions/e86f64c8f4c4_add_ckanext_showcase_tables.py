"""Add ckanext-showcase tables

Revision ID: e86f64c8f4c4
Revises: 
Create Date: 2026-01-08 10:54:18.057672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e86f64c8f4c4'
down_revision = None
branch_labels = None
depends_on = None

# Copied from ckanext-showcase

def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if "showcase_package_association" not in tables:
        op.create_table(
            "showcase_package_association",
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
    if "showcase_package_association" not in tables:
        op.create_table(
            "showcase_admin",
            sa.Column(
                "user_id",
                sa.UnicodeText,
                sa.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )


def downgrade():
    op.drop_table("showcase_package_association")
    op.drop_table("showcase_admin")
