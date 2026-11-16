"""
Роутер вспомогательных справочников (домены, группы, источники, офферы).

Предоставляет списки опций для выпадающих меню веб-интерфейса.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from core.logger import get_logger
from integrations.keitaro import keitaro_client

router = APIRouter(prefix="/api/dictionaries", tags=["Dictionaries"])
log = get_logger("dictionaries_router")


@router.get("/offers", response_model=List[Dict[str, Any]])
async def get_offers() -> List[Dict[str, Any]]:
    """Возвращает список доступных офферов для выбора."""
    try:
        return await keitaro_client.get_offers()
    except Exception as exc:
        log.error(f"Ошибка получения списка офферов: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/domains", response_model=List[Dict[str, Any]])
async def get_domains() -> List[Dict[str, Any]]:
    """Возвращает список доменов трекера."""
    try:
        return await keitaro_client.get_domains()
    except Exception as exc:
        log.error(f"Ошибка получения доменов: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/groups", response_model=List[Dict[str, Any]])
async def get_groups() -> List[Dict[str, Any]]:
    """Возвращает группы кампаний."""
    try:
        return await keitaro_client.get_groups()
    except Exception as exc:
        log.error(f"Ошибка получения групп: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_sources() -> List[Dict[str, Any]]:
    """Возвращает источники трафика."""
    try:
        return await keitaro_client.get_traffic_sources()
    except Exception as exc:
        log.error(f"Ошибка получения источников: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
