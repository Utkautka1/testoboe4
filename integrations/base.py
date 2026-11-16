"""
Базовый абстрактный класс интеграции с внешними API.

Реализует общий жизненный цикл HTTP-клиента, контекстный менеджер
и управление таймаутами.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx


class BaseIntegration(ABC):
    """Абстрактный класс внешней интеграции."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Возвращает или инициализирует асинхронный HTTP-клиент."""
        import asyncio
        loop = asyncio.get_running_loop()
        if (
            self._client is None
            or self._client.is_closed
            or getattr(self, "_loop", None) is not loop
        ):
            self._loop = loop
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Закрывает HTTP-сессию."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def ping(self) -> bool:
        """Проверка работоспособности сервиса."""
        raise NotImplementedError
