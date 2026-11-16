"""
Бизнес-логика создания кампаний с потоками Google и Offers.

Инкапсулирует алгоритм создания двух потоков, привязку гео-фильтров
и расчет распределения долей офферов.
"""

import uuid
from typing import Any, Dict, List
from config import settings
from core.logger import get_logger
from integrations.keitaro import keitaro_client

log = get_logger("campaign_creator")


def build_alias(name: str) -> str:
    """Генерирует уникальный alias для кампании в Keitaro."""
    cleaned = "".join(c if c.isalnum() else "-" for c in name.lower())
    short_uuid = uuid.uuid4().hex[:6]
    return f"{cleaned[:30]}-{short_uuid}"


def calculate_equal_shares(count: int) -> List[int]:
    """
    Равномерно делит 100% между офферами.
    Остаток прибавляется к первому элементу.
    """
    if count <= 0:
        return []
    base_share = 100 // count
    remainder = 100 % count
    shares = [base_share] * count
    shares[0] += remainder
    return shares


async def create_google_stream(campaign_id: int, geo_country: str) -> Dict[str, Any]:
    """Создает первый поток: ловит указанное гео и редиректит на Google."""
    payload = {
        "campaign_id": campaign_id,
        "name": "Google",
        "type": "regular",
        "position": 1,
        "action_type": "http",
        "action_payload": "https://www.google.com",
        "schema": "redirect",
        "collect_clicks": True,
        "filters": [
            {
                "name": "country",
                "mode": "accept",
                "payload": [geo_country.upper()],
            }
        ],
        "landings": [],
        "offers": [],
    }
    return await keitaro_client.create_stream(payload)


async def create_offers_stream(campaign_id: int, offer_id: int) -> Dict[str, Any]:
    """Создает второй поток: отправляет на выбранный оффер."""
    payload = {
        "campaign_id": campaign_id,
        "name": "Offers",
        "type": "regular",
        "position": 2,
        "action_type": "http",
        "action_payload": "",
        "schema": "landings",
        "collect_clicks": True,
        "filters": [],
        "landings": [],
        "offers": [
            {
                "offer_id": offer_id,
                "state": "active",
                "share": 100,
            }
        ],
    }
    return await keitaro_client.create_stream(payload)
