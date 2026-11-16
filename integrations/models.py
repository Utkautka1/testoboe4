"""
Модели данных для интеграции с сервисом Keitaro.

Используются для строгой валидации входов и выходов при общении
с API трекера Keitaro.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KeitaroDomainItem(BaseModel):
    """Модель элемента домена из Keitaro."""
    value: int
    name: str
    group_id: Optional[int] = None
    group: Optional[str] = None


class KeitaroGroupItem(BaseModel):
    """Модель группы кампаний."""
    value: int
    name: str


class KeitaroSourceItem(BaseModel):
    """Модель источника трафика."""
    id: int
    name: str


class KeitaroOfferItem(BaseModel):
    """Модель оффера для селектора и привязки."""
    value: int
    name: str
    group_id: Optional[int] = None
    group: Optional[str] = None


class KeitaroStreamFilter(BaseModel):
    """Модель правила фильтрации потока (например, по стране)."""
    name: str = "country"
    mode: str = "accept"
    payload: List[str]


class KeitaroStreamOffer(BaseModel):
    """Модель оффера внутри потока."""
    offer_id: int
    share: int = 100
    state: str = "active"


class KeitaroStream(BaseModel):
    """Модель потока в кампании Keitaro."""
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    name: str
    type: str = "regular"
    position: int = 1
    action_type: str = "http"
    action_payload: str = ""
    schema_name: str = Field(default="redirect", alias="schema")
    collect_clicks: bool = True
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    offers: List[Dict[str, Any]] = Field(default_factory=list)
