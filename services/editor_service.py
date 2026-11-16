"""
Сервис двухфазного редактирования офферов в потоках Keitaro.

Реализует полный цикл:
1. Fetch Streams (синхронизация с Keitaro и отслеживание удаленных офферов).
2. Черновые изменения (добавление, удаление, bring back, пин веса) с подсветкой потока желтым.
3. Отмена черновика (Cancel).
4. Публикация в Keitaro (Push to Keitaro).
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.logger import get_logger
from core.psql import async_db_session
from db.psql.models.models import CampaignModel, CampaignOfferModel
from integrations.keitaro import keitaro_client
from services.shares_calculator import calculate_pinned_shares

log = get_logger("editor_service")


async def get_or_create_local_campaign(keitaro_id: int) -> CampaignModel:
    """Находит кампанию в локальной БД или создает запись по данным Keitaro."""
    async with async_db_session() as session:
        stmt = (
            select(CampaignModel)
            .where(CampaignModel.keitaro_id == keitaro_id)
            .options(selectinload(CampaignModel.offers))
        )
        res = await session.execute(stmt)
        campaign = res.scalar_one_or_none()
        if not campaign:
            remote = await keitaro_client.get_campaign(keitaro_id)
            campaign = CampaignModel(
                keitaro_id=keitaro_id,
                name=remote.get("name", f"Campaign_{keitaro_id}"),
                alias=remote.get("alias", f"alias-{keitaro_id}"),
                domain_id=remote.get("domain_id"),
                group_id=remote.get("group_id"),
                traffic_source_id=remote.get("traffic_source_id"),
            )
            session.add(campaign)
            await session.commit()
            await session.refresh(campaign)
        return campaign


def _update_or_create_stream_offers(
    session, campaign_id: int, stream: Dict[str, Any],
    existing: Dict[int, CampaignOfferModel], all_offers_dict: Dict[int, str],
) -> set[int]:
    """Обновляет активные офферы потока и создает новые при необходимости."""
    remote_ids = set()
    for ro in stream.get("offers", []):
        oid = ro["offer_id"]
        remote_ids.add(oid)
        if oid in existing:
            existing[oid].status = "active"
            existing[oid].is_published = True
            existing[oid].share = ro.get("share", 100)
            existing[oid].stream_id = stream["id"]
        else:
            session.add(CampaignOfferModel(
                campaign_id=campaign_id, stream_id=stream["id"],
                keitaro_offer_id=oid, offer_name=all_offers_dict.get(oid, f"Offer #{oid}"),
                share=ro.get("share", 100), status="active", is_published=True,
            ))
    return remote_ids


async def sync_streams_from_keitaro(campaign_id: int) -> Dict[str, Any]:
    """Синхронизирует потоки из Keitaro (кнопка Fetch Streams)."""
    campaign = await get_or_create_local_campaign(campaign_id)
    remote_streams = await keitaro_client.get_campaign_streams(campaign_id)
    all_offers_dict = {o["value"]: o["name"] for o in await keitaro_client.get_offers()}

    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(CampaignOfferModel.campaign_id == campaign.id)
        existing = {o.keitaro_offer_id: o for o in (await session.execute(stmt)).scalars().all()}

        for stream in remote_streams:
            if len(stream.get("offers", [])) > 0 or stream.get("name", "").lower() == "offers":
                remote_ids = _update_or_create_stream_offers(
                    session, campaign.id, stream, existing, all_offers_dict
                )
                for oid, off_obj in existing.items():
                    if oid not in remote_ids and off_obj.is_published:
                        off_obj.status = "removed"
                        off_obj.share = 0

        await session.commit()
    return await get_campaign_editor_state(campaign_id)


def _format_stream_views(remote_streams: List[Dict[str, Any]], is_dirty: bool) -> List[Dict[str, Any]]:
    """Форматирует отображение потоков с флагом dirty."""
    return [
        {
            "id": s["id"], "name": s["name"],
            "has_offers": len(s.get("offers", [])) > 0 or s.get("name", "").lower() == "offers",
            "is_dirty": is_dirty if (len(s.get("offers", [])) > 0 or s.get("name", "").lower() == "offers") else False,
            "action_type": s.get("action_type"), "action_payload": s.get("action_payload"),
            "filters": s.get("filters", []),
        } for s in remote_streams
    ]


def _build_editor_view(
    campaign: CampaignModel,
    db_offers: List[CampaignOfferModel],
    remote_streams: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Формирует структуру ответа редактора для клиентского интерфейса."""
    is_dirty = any(not o.is_published or o.status.startswith("pending") for o in db_offers)
    offers_data = [
        {
            "id": o.id, "offer_id": o.keitaro_offer_id,
            "name": o.offer_name or f"Offer #{o.keitaro_offer_id}",
            "share": o.share, "is_pinned": o.is_pinned,
            "status": o.status, "is_published": o.is_published,
        } for o in db_offers
    ]
    return {
        "campaign_id": campaign.keitaro_id, "name": campaign.name,
        "alias": campaign.alias, "is_dirty": is_dirty,
        "streams": _format_stream_views(remote_streams, is_dirty),
        "offers": offers_data,
    }


async def get_campaign_editor_state(campaign_id: int) -> Dict[str, Any]:
    """Возвращает полное состояние редактора для фронтенда."""
    campaign = await get_or_create_local_campaign(campaign_id)
    remote_streams = await keitaro_client.get_campaign_streams(campaign_id)
    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(CampaignOfferModel.campaign_id == campaign.id)
        db_offers = list((await session.execute(stmt)).scalars().all())
    return _build_editor_view(campaign, db_offers, remote_streams)


def _upsert_offer_in_session(session, campaign_id: int, offer_id: int, offer_name: Optional[str], existing) -> None:
    """Создает новый черновой оффер или обновляет статус существующего."""
    if existing:
        existing.status = "pending_add"
        existing.is_published = False
    else:
        session.add(CampaignOfferModel(
            campaign_id=campaign_id,
            keitaro_offer_id=offer_id,
            offer_name=offer_name or f"Offer #{offer_id}",
            status="pending_add",
            is_published=False,
        ))


async def add_offer_draft(campaign_id: int, offer_id: int, offer_name: Optional[str] = None) -> Dict[str, Any]:
    """Черновое добавление оффера в поток с автоматическим пересчетом долей."""
    campaign = await get_or_create_local_campaign(campaign_id)
    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(
            CampaignOfferModel.campaign_id == campaign.id,
            CampaignOfferModel.keitaro_offer_id == offer_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        _upsert_offer_in_session(session, campaign.id, offer_id, offer_name, existing)
        await session.commit()
        await _recalculate_and_save_shares(campaign.id, session)

    return await get_campaign_editor_state(campaign_id)


async def remove_offer_draft(campaign_id: int, offer_id: int) -> Dict[str, Any]:
    """Черновое удаление оффера из потока (пометка pending_del)."""
    campaign = await get_or_create_local_campaign(campaign_id)
    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(
            CampaignOfferModel.campaign_id == campaign.id,
            CampaignOfferModel.keitaro_offer_id == offer_id,
        )
        off = (await session.execute(stmt)).scalar_one_or_none()
        if off:
            if off.is_published:
                off.status = "pending_del"
            else:
                await session.delete(off)
            await session.commit()
            await _recalculate_and_save_shares(campaign.id, session)

    return await get_campaign_editor_state(campaign_id)


async def bring_back_offer_draft(campaign_id: int, offer_id: int) -> Dict[str, Any]:
    """Возврат удаленного оффера (Bring back) в черновик потока."""
    campaign = await get_or_create_local_campaign(campaign_id)
    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(
            CampaignOfferModel.campaign_id == campaign.id,
            CampaignOfferModel.keitaro_offer_id == offer_id,
        )
        off = (await session.execute(stmt)).scalar_one_or_none()
        if off:
            off.status = "pending_add"
            off.is_published = False
            await session.commit()
            await _recalculate_and_save_shares(campaign.id, session)

    return await get_campaign_editor_state(campaign_id)


async def toggle_pin_offer(campaign_id: int, offer_id: int, is_pinned: bool) -> Dict[str, Any]:
    """Фиксация (Pin) или открепление веса оффера."""
    campaign = await get_or_create_local_campaign(campaign_id)
    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(
            CampaignOfferModel.campaign_id == campaign.id,
            CampaignOfferModel.keitaro_offer_id == offer_id,
        )
        off = (await session.execute(stmt)).scalar_one_or_none()
        if off:
            off.is_pinned = is_pinned
            await session.commit()
            await _recalculate_and_save_shares(campaign.id, session)

    return await get_campaign_editor_state(campaign_id)


async def cancel_drafts(campaign_id: int) -> Dict[str, Any]:
    """Отмена всех неопубликованных черновиков (Cancel) и возврат к Keitaro."""
    campaign = await get_or_create_local_campaign(campaign_id)
    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(CampaignOfferModel.campaign_id == campaign.id)
        offers = list((await session.execute(stmt)).scalars().all())

        for o in offers:
            if not o.is_published:
                await session.delete(o)
            elif o.status == "pending_del":
                o.status = "active"

        await session.commit()
        await _recalculate_and_save_shares(campaign.id, session)

    return await get_campaign_editor_state(campaign_id)


def _prepare_keitaro_payload(offers: List[CampaignOfferModel]) -> List[Dict[str, Any]]:
    """Готовит список офферов для отправки в API Keitaro."""
    payload = []
    for o in offers:
        if o.status in ("active", "pending_add"):
            o.status = "active"
            o.is_published = True
            payload.append({"offer_id": o.keitaro_offer_id, "share": o.share, "state": "active"})
        elif o.status == "pending_del":
            o.status = "removed"
            o.is_published = True
            o.share = 0
    return payload


async def push_to_keitaro(campaign_id: int) -> Dict[str, Any]:
    """Публикация изменений в Keitaro (Push to Keitaro)."""
    campaign = await get_or_create_local_campaign(campaign_id)
    remote_streams = await keitaro_client.get_campaign_streams(campaign_id)
    target_stream = next(
        (s for s in remote_streams if len(s.get("offers", [])) > 0 or s.get("name", "").lower() == "offers"),
        remote_streams[-1] if remote_streams else None,
    )
    if not target_stream:
        raise ValueError("Поток для офферов не найден")

    async with async_db_session() as session:
        stmt = select(CampaignOfferModel).where(CampaignOfferModel.campaign_id == campaign.id)
        offers = list((await session.execute(stmt)).scalars().all())
        keitaro_offers_payload = _prepare_keitaro_payload(offers)
        await session.commit()

    await keitaro_client.update_stream({"id": target_stream["id"], "offers": keitaro_offers_payload})
    return await get_campaign_editor_state(campaign_id)


async def _recalculate_and_save_shares(campaign_id: int, session) -> None:
    """Вспомогательная функция пересчета и сохранения долей в сессии."""
    stmt = select(CampaignOfferModel).where(CampaignOfferModel.campaign_id == campaign_id)
    db_offers = list((await session.execute(stmt)).scalars().all())

    offers_dict = [
        {
            "id": o.id,
            "status": "removed" if o.status in ("removed", "pending_del") else "active",
            "is_pinned": o.is_pinned,
            "share": o.share,
        }
        for o in db_offers
    ]

    calculated = calculate_pinned_shares(offers_dict)
    for off_model in db_offers:
        match = next((c for c in calculated if c["id"] == off_model.id), None)
        if match:
            off_model.share = match["share"]

    await session.commit()
