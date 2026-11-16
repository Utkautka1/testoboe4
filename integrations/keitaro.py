"""
Клиент интеграции с трекером Keitaro.

Реализует авторизацию по сессии и API-ключу, получение справочников,
создание кампаний с потоками редиректа и офферов, а также редактирование офферов.
"""

import uuid
from typing import Any, Dict, List, Optional
import httpx

from config import settings
from core.logger import get_logger
from integrations.base import BaseIntegration

log = get_logger("keitaro_client")


class KeitaroClient(BaseIntegration):
    """Клиент для взаимодействия с API Keitaro с кэшированием справочников."""

    def __init__(self):
        super().__init__(base_url=settings.KEITARO_BASE_URL, timeout=30.0)
        self.login = settings.KEITARO_LOGIN
        self.password = settings.KEITARO_PASSWORD
        self._auth_cookies: Optional[httpx.Cookies] = None
        self._cached_offers: Optional[List[Dict[str, Any]]] = None
        self._cached_campaigns: Optional[List[Dict[str, Any]]] = None
        self._cache_time: float = 0

    async def authenticate(self) -> bool:
        """
        Выполняет аутентификацию в Keitaro и сохраняет cookies сессии.
        """
        client = await self.get_client()
        url = "/admin/?object=auth.login"
        payload = {"login": self.login, "password": self.password}
        try:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                self._auth_cookies = res.cookies
                log.info("✅ Успешная аутентификация в Keitaro")
                return True
            log.error(f"Ошибка аутентификации Keitaro: {res.status_code} {res.text}")
            return False
        except Exception as exc:
            log.error(f"Исключение при входе в Keitaro: {exc}")
            return False

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """
        Выполняет авторизованный запрос с автоматическим логином при 401/403.
        """
        client = await self.get_client()
        if not self._auth_cookies:
            await self.authenticate()
        
        cookies = kwargs.pop("cookies", self._auth_cookies)
        res = await client.request(method, path, cookies=cookies, **kwargs)
        if res.status_code in (401, 403):
            log.warning("Сессия Keitaro истекла, переавторизация...")
            if await self.authenticate():
                res = await client.request(method, path, cookies=self._auth_cookies, **kwargs)
        
        if res.status_code >= 400:
            log.error(f"Keitaro API error {res.status_code}: {res.text}")
        res.raise_for_status()
        return res.json()

    async def ping(self) -> bool:
        """Проверяет доступность сервиса Keitaro."""
        try:
            data = await self._request("GET", "/admin/?object=system.trackerInfo")
            return bool(data.get("users_count") or data.get("domains_count"))
        except Exception:
            return False

    async def get_domains(self) -> List[Dict[str, Any]]:
        """Возвращает список доступных доменов."""
        return await self._request("GET", "/admin/?object=domains.listAsOptions")

    async def get_groups(self) -> List[Dict[str, Any]]:
        """Возвращает список групп кампаний."""
        return await self._request("GET", "/admin/?object=groups.listAsOptions&type=campaigns")

    async def get_traffic_sources(self) -> List[Dict[str, Any]]:
        """Возвращает список источников трафика."""
        return await self._request("GET", "/admin/?object=trafficSources.index&valueProp=id")

    async def get_offers(self, force: bool = False) -> List[Dict[str, Any]]:
        """Возвращает список офферов трекера с кэшированием на 60 секунд."""
        import time
        now = time.time()
        if not force and self._cached_offers and (now - self._cache_time < 60):
            return self._cached_offers
        self._cached_offers = await self._request("GET", "/admin/?object=offers.listAsOptions")
        self._cache_time = now
        return self._cached_offers

    async def get_campaigns(self, force: bool = False) -> List[Dict[str, Any]]:
        """Возвращает список кампаний трекера через сессионный API с кэшем на 10 сек."""
        import time
        now = time.time()
        if not force and self._cached_campaigns and (now - getattr(self, "_camp_cache_time", 0) < 10):
            return self._cached_campaigns
        self._cached_campaigns = await self._request("GET", "/admin/?object=campaigns.listAsOptions")
        self._camp_cache_time = now
        return self._cached_campaigns

    async def get_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Возвращает детальную информацию о кампании."""
        return await self._request("GET", f"/admin/?object=campaigns.show&id={campaign_id}")

    async def get_campaign_streams(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Возвращает список потоков кампании."""
        return await self._request("GET", f"/admin/?object=streams.index&campaign_id={campaign_id}")

    async def create_campaign(
        self,
        name: str,
        alias: str,
        domain_id: int,
        group_id: int,
        traffic_source_id: int,
    ) -> Dict[str, Any]:
        """Создает базовую кампанию в Keitaro."""
        payload = {
            "name": name,
            "alias": alias,
            "domain_id": domain_id,
            "group_id": group_id,
            "traffic_source_id": traffic_source_id,
            "cost_type": "CPC",
            "cost_value": 0,
            "cost_currency": "USD",
        }
        return await self._request("POST", "/admin/?object=campaigns.create", json=payload)

    async def create_stream(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Создает поток для кампании."""
        return await self._request("POST", "/admin/?object=streams.create", json=payload)

    async def update_stream(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет поток (например, набор офферов и их распределение)."""
        return await self._request("POST", "/admin/?object=streams.update", json=payload)


# Глобальный синглтон клиента
keitaro_client = KeitaroClient()
