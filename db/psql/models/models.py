"""
Модели таблиц базы данных PostgreSQL для управления кампаниями и офферами.

Поддерживают двухфазное редактирование потоков Keitaro:
статусы 'published', 'pending_addition', 'pending_removal', 'removed',
флаг фиксации доли (is_pinned) и хранение черновика распределения.
"""

from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.psql import Base
from db.psql.crud.base import ModelAdmin
from db.psql.models.columns import created_at, intpk, str_32, str_140, str_255, updated_at
from db.psql.models.enum import CampaignState


class CampaignModel(Base, ModelAdmin["CampaignModel"]):
    """Локальная таблица кампаний, созданных или импортированных из Keitaro."""
    __tablename__ = "campaigns"

    id: Mapped[intpk]
    keitaro_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str_140] = mapped_column(index=True)
    alias: Mapped[str_140] = mapped_column(unique=True)
    geo_country: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    domain_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    traffic_source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state: Mapped[str_32] = mapped_column(default=CampaignState.ACTIVE.value)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    offers: Mapped[List["CampaignOfferModel"]] = relationship(
        "CampaignOfferModel",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )


class CampaignOfferModel(Base, ModelAdmin["CampaignOfferModel"]):
    """
    Таблица привязки офферов к кампании и потоку.

    Хранит статус (active, removed, pending_add, pending_del),
    флаг пина веса (is_pinned) и текущий расчетный вес (share).
    """
    __tablename__ = "campaign_offers"

    id: Mapped[intpk]
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    stream_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    keitaro_offer_id: Mapped[int] = mapped_column(BigInteger, index=True)
    offer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    share: Mapped[int] = mapped_column(Integer, default=100)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, removed, pending_add, pending_del
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[created_at]

    campaign: Mapped["CampaignModel"] = relationship("CampaignModel", back_populates="offers")
