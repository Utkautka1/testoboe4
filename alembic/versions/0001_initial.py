"""Initial migration: campaigns and campaign_offers

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-16 20:30:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keitaro_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("alias", sa.String(length=140), nullable=False),
        sa.Column("geo_country", sa.String(length=32), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("traffic_source_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('Europe/Moscow', NOW())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('Europe/Moscow', NOW())"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alias"),
    )
    op.create_index(op.f("ix_campaigns_keitaro_id"), "campaigns", ["keitaro_id"], unique=True)
    op.create_index(op.f("ix_campaigns_name"), "campaigns", ["name"], unique=False)

    op.create_table(
        "campaign_offers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("keitaro_offer_id", sa.BigInteger(), nullable=False),
        sa.Column("offer_name", sa.String(length=255), nullable=True),
        sa.Column("share", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('Europe/Moscow', NOW())"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_campaign_offers_campaign_id"), "campaign_offers", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_campaign_offers_keitaro_offer_id"), "campaign_offers", ["keitaro_offer_id"], unique=False)


def downgrade() -> None:
    op.drop_table("campaign_offers")
    op.drop_table("campaigns")
