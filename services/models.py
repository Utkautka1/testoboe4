"""
Pydantic-схемы для сервиса управления кампаниями.

Определяют контракты запросов и ответов для создания кампаний,
добавления и удаления офферов, а также валидации входных данных.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CampaignCreateRequest(BaseModel):
    """Схема запроса на создание кампании."""
    name: str = Field(..., min_length=2, max_length=100, description="Название кампании")
    geo_country: str = Field(..., min_length=2, max_length=2, description="Двухбуквенный гео-код (ISO)")
    offer_id: int = Field(..., gt=0, description="ID оффера в Keitaro")
    domain_id: Optional[int] = Field(None, description="Опциональный кастомный ID домена")
    group_id: Optional[int] = Field(None, description="Опциональный кастомный ID группы")
    traffic_source_id: Optional[int] = Field(None, description="Опциональный кастомный ID источника")


class StreamOfferInfo(BaseModel):
    """Информация об оффере в потоке."""
    id: Optional[int] = None
    offer_id: int
    offer_name: Optional[str] = None
    share: int
    state: str = "active"


class StreamInfo(BaseModel):
    """Информация о потоке кампании."""
    id: int
    name: str
    type: str
    position: int
    action_type: str
    action_payload: str
    schema_name: str
    filters: List[Dict[str, Any]]
    offers: List[StreamOfferInfo]


class CampaignDetailResponse(BaseModel):
    """Детальная информация о кампании с её потоками."""
    id: int
    name: str
    alias: str
    domain_id: Optional[int] = None
    group_id: Optional[int] = None
    traffic_source_id: Optional[int] = None
    state: str
    streams: List[StreamInfo]


class CampaignSummary(BaseModel):
    """Краткая информация о кампании для списков."""
    id: int
    name: str
    alias: str
    group: Optional[str] = None
    state: str
    streams_count: Optional[int] = None


class OfferAddRequest(BaseModel):
    """Запрос на добавление оффера в кампанию."""
    offer_id: int = Field(..., gt=0, description="ID оффера для добавления")


class OfferDistribution(BaseModel):
    """Схема распределения долей офферов."""
    offer_id: int
    share: int
