"""
Pydantic-схемы API запросов и ответов для эндпоинтов кампаний и редактора.

Валидируют входящие данные веб-клиента и сериализуют ответы роутеров.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CampaignCreateSchema(BaseModel):
    """Схема создания кампании через REST API."""
    name: str = Field(..., min_length=2, max_length=80)
    geo_country: str = Field(..., min_length=2, max_length=2)
    offer_id: int = Field(..., gt=0)


class CampaignCreateResponse(BaseModel):
    """Схема ответа после создания кампании."""
    success: bool
    campaign_id: int
    name: str
    alias: str
    message: str


class OfferActionSchema(BaseModel):
    """Схема запроса на добавление оффера в черновик."""
    offer_id: int = Field(..., gt=0)
    offer_name: Optional[str] = None


class OfferPinSchema(BaseModel):
    """Схема закрепления/открепления доли оффера."""
    offer_id: int = Field(..., gt=0)
    is_pinned: bool
