"""
Роутер эндпоинтов управления кампаниями и расширенного редактора Keitaro.

Реализует создание кампаний и полный двухфазный цикл редактор:
Fetch Streams, Add Offer, Remove Offer, Bring Back, Pin Share, Cancel, Push to Keitaro.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from api.schemas.campaigns import (
    CampaignCreateResponse,
    CampaignCreateSchema,
    OfferActionSchema,
    OfferPinSchema,
)
from config import settings
from core.logger import get_logger
from integrations.keitaro import keitaro_client
from services.creator_service import build_alias, create_google_stream, create_offers_stream
from services.editor_service import (
    add_offer_draft,
    bring_back_offer_draft,
    cancel_drafts,
    get_campaign_editor_state,
    push_to_keitaro,
    remove_offer_draft,
    sync_streams_from_keitaro,
    toggle_pin_offer,
)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])
log = get_logger("campaigns_router")


@router.get("", response_model=List[Dict[str, Any]])
async def list_campaigns() -> List[Dict[str, Any]]:
    """Возвращает список кампаний из Keitaro."""
    try:
        return await keitaro_client.get_campaigns()
    except Exception as exc:
        log.error(f"Ошибка получения кампаний: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


async def provision_campaign(name: str, geo_country: str, offer_id: int) -> dict:
    """Создает базовую кампанию и настраивает потоки."""
    full_name = f"{settings.CAMPAIGN_PREFIX}{name}"
    alias = build_alias(full_name)
    camp = await keitaro_client.create_campaign(
        name=full_name,
        alias=alias,
        domain_id=settings.KEITARO_DEFAULT_DOMAIN_ID,
        group_id=settings.KEITARO_DEFAULT_GROUP_ID,
        traffic_source_id=settings.KEITARO_DEFAULT_SOURCE_ID,
    )
    camp_id = camp["id"]
    await create_google_stream(camp_id, geo_country)
    await create_offers_stream(camp_id, offer_id)
    await sync_streams_from_keitaro(camp_id)
    return {"id": camp_id, "name": full_name, "alias": alias}


@router.post("", response_model=CampaignCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(payload: CampaignCreateSchema) -> CampaignCreateResponse:
    """Создает новую кампанию с потоком Google и потоком офферов."""
    try:
        camp_info = await provision_campaign(payload.name, payload.geo_country, payload.offer_id)
        log.info(f"✅ Кампания {camp_info['id']} ({camp_info['name']}) создана")
        return CampaignCreateResponse(
            success=True,
            campaign_id=camp_info["id"],
            name=camp_info["name"],
            alias=camp_info["alias"],
            message="Кампания успешно создана с настроенными потоками",
        )
    except Exception as exc:
        log.error(f"Ошибка при создании кампании: {exc}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания кампании: {exc}")


@router.get("/{campaign_id}/editor")
async def get_editor_state(campaign_id: int) -> Dict[str, Any]:
    """Возвращает текущее состояние редактора кампании."""
    try:
        return await get_campaign_editor_state(campaign_id)
    except Exception as exc:
        log.error(f"Ошибка получения редактора: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/fetch_streams")
async def fetch_streams(campaign_id: int) -> Dict[str, Any]:
    """Кнопка 'Fetch Streams': синхронизация потоков из Keitaro с отслеживанием удалений."""
    try:
        return await sync_streams_from_keitaro(campaign_id)
    except Exception as exc:
        log.error(f"Ошибка синхронизации потоков: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/draft_offer")
async def add_draft_offer(campaign_id: int, payload: OfferActionSchema) -> Dict[str, Any]:
    """Черновое добавление оффера в поток с пересчетом долей."""
    try:
        return await add_offer_draft(campaign_id, payload.offer_id, payload.offer_name)
    except Exception as exc:
        log.error(f"Ошибка добавления оффера: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/remove_offer")
async def remove_draft_offer(campaign_id: int, payload: OfferActionSchema) -> Dict[str, Any]:
    """Черновое удаление оффера из потока (серый цвет, share=0%)."""
    try:
        return await remove_offer_draft(campaign_id, payload.offer_id)
    except Exception as exc:
        log.error(f"Ошибка удаления оффера: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/bring_back_offer")
async def bring_back_offer(campaign_id: int, payload: OfferActionSchema) -> Dict[str, Any]:
    """Возврат удаленного оффера (кнопка Bring Back)."""
    try:
        return await bring_back_offer_draft(campaign_id, payload.offer_id)
    except Exception as exc:
        log.error(f"Ошибка возврата оффера: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/pin_offer")
async def pin_offer(campaign_id: int, payload: OfferPinSchema) -> Dict[str, Any]:
    """Фиксация (Pin) или открепление доли оффера."""
    try:
        return await toggle_pin_offer(campaign_id, payload.offer_id, payload.is_pinned)
    except Exception as exc:
        log.error(f"Ошибка закрепления веса: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/cancel")
async def cancel_changes(campaign_id: int) -> Dict[str, Any]:
    """Кнопка 'Cancel': откат всех неопубликованных черновиков."""
    try:
        return await cancel_drafts(campaign_id)
    except Exception as exc:
        log.error(f"Ошибка отмены черновика: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{campaign_id}/push")
async def push_changes(campaign_id: int) -> Dict[str, Any]:
    """Кнопка 'Push to Keitaro': применение и сохранение изменений в трекере."""
    try:
        return await push_to_keitaro(campaign_id)
    except Exception as exc:
        log.error(f"Ошибка публикации в Keitaro: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
