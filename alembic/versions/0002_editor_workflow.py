"""Update campaign_offers schema for editor workflow

Revision ID: 0002_editor_workflow
Revises: 0001_initial
Create Date: 2026-11-16 21:55:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_editor_workflow"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("campaigns", "geo_country", existing_type=sa.String(length=32), nullable=True)
    op.alter_column("campaigns", "domain_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("campaigns", "group_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("campaigns", "traffic_source_id", existing_type=sa.Integer(), nullable=True)

    op.add_column("campaign_offers", sa.Column("stream_id", sa.BigInteger(), nullable=True))
    op.add_column("campaign_offers", sa.Column("is_pinned", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("campaign_offers", sa.Column("status", sa.String(length=32), server_default="active", nullable=False))
    op.add_column("campaign_offers", sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False))
    op.create_index(op.f("ix_campaign_offers_stream_id"), "campaign_offers", ["stream_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_campaign_offers_stream_id"), table_name="campaign_offers")
    op.drop_column("campaign_offers", "is_published")
    op.drop_column("campaign_offers", "status")
    op.drop_column("campaign_offers", "is_pinned")
    op.drop_column("campaign_offers", "stream_id")
