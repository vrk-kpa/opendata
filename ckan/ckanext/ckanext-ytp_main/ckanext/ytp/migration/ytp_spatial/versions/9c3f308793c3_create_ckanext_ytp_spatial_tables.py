"""Create ckanext-ytp_spatial tables

Revision ID: 9c3f308793c3
Revises: 
Create Date: 2026-01-12 08:44:02.350177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c3f308793c3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()

    if "municipality_bounding_boxes" not in tables:
        op.create_table(
            "municipality_bounding_boxes",
            sa.Column("name", sa.UnicodeText, nullable=False, primary_key=True),
            sa.Column("lat_min", sa.UnicodeText, nullable=False),
            sa.Column("lat_max", sa.UnicodeText, nullable=False),
            sa.Column("lng_min", sa.UnicodeText, nullable=False),
            sa.Column("lng_max", sa.UnicodeText, nullable=False),
        )


def downgrade():
    op.drop_table('municipality_bounding_boxes')
