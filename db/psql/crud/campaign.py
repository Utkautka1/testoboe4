"""
CRUD-методы для работы с кампаниями в базе данных.

Содержит атомарные функции сохранения кампании со связанными офферами
и выборки по внешнему идентификатору Keitaro.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.psql import async_db_session
from db.psql.models.models import CampaignModel, CampaignOfferModel


async def get_campaign_by_keitaro_id(keitaro_id: int) -> Optional[CampaignModel]:
    """Получает кампанию из БД по идентификатору Keitaro."""
    async with async_db_session() as session:
        stmt = (
            select(CampaignModel)
            .where(CampaignModel.keitaro_id == keitaro_id)
            .options(selectinload(CampaignModel.offers))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def list_local_campaigns(limit: int = 100) -> List[CampaignModel]:
    """Возвращает список сохраненных локально кампаний."""
    async with async_db_session() as session:
        stmt = (
            select(CampaignModel)
            .order_by(CampaignModel.id.desc())
            .options(selectinload(CampaignModel.offers))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


def create_campaign_instances(
    keitaro_id: int, name: str, alias: str, geo_country: str,
    domain_id: int, group_id: int, traffic_source_id: int,
    offer_id: int, offer_name: Optional[str],
) -> tuple[CampaignModel, CampaignOfferModel]:
    """Создает инстансы моделей кампании и первого оффера."""
    campaign = CampaignModel(
        keitaro_id=keitaro_id, name=name, alias=alias,
        geo_country=geo_country, domain_id=domain_id,
        group_id=group_id, traffic_source_id=traffic_source_id,
    )
    offer = CampaignOfferModel(
        keitaro_offer_id=offer_id,
        offer_name=offer_name, share=100,
    )
    campaign.offers.append(offer)
    return campaign, offer


async def save_campaign_with_offer(
    keitaro_id: int,
    name: str,
    alias: str,
    geo_country: str,
    domain_id: int,
    group_id: int,
    traffic_source_id: int,
    offer_id: int,
    offer_name: Optional[str] = None,
) -> CampaignModel:
    """Сохраняет новую кампанию и оффер в транзакции."""
    campaign, _ = create_campaign_instances(
        keitaro_id, name, alias, geo_country,
        domain_id, group_id, traffic_source_id,
        offer_id, offer_name
    )
    async with async_db_session() as session:
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        return campaign
