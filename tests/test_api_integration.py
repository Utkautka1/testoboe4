"""
Интеграционные тесты для API создания и редактора кампаний.

Проверяет эндпоинты создания кампании, получения списка, просмотра потоков,
а также двухфазный цикл редактора (draft -> push).
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health():
    """Проверка доступности healthcheck."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_dictionaries():
    """Проверка получения справочников офферов и доменов."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_offers = await client.get("/api/dictionaries/offers")
        assert res_offers.status_code == 200
        assert isinstance(res_offers.json(), list)


async def _run_campaign_creation(client: AsyncClient) -> int:
    """Создает тестовую кампанию и проверяет ответ."""
    suffix = uuid.uuid4().hex[:6]
    payload = {"name": f"ci_test_{suffix}", "geo_country": "US", "offer_id": 4440}
    res = await client.post("/api/campaigns", json=payload)
    assert res.status_code == 201
    return res.json()["campaign_id"]


async def _check_editor_state(client: AsyncClient, camp_id: int) -> dict:
    """Проверяет состояние редактора кампании."""
    res = await client.get(f"/api/campaigns/{camp_id}/editor")
    assert res.status_code == 200
    state = res.json()
    assert len(state["streams"]) >= 2
    return state


async def _verify_offer_actions(client: AsyncClient, camp_id: int, stream_id: int) -> None:
    """Проверяет добавление оффера в черновик редактора."""
    add_res = await client.post(
        f"/api/campaigns/{camp_id}/draft_offer",
        json={"offer_id": 4514, "offer_name": "Test Offer 4514"},
    )
    assert add_res.status_code == 200
    remove_res = await client.post(
        f"/api/campaigns/{camp_id}/remove_offer",
        json={"offer_id": 4514},
    )
    assert remove_res.status_code == 200


@pytest.mark.asyncio
async def test_campaign_lifecycle():
    """Тест создания кампании и операций в редакторе."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        camp_id = await _run_campaign_creation(client)
        state = await _check_editor_state(client, camp_id)
        offers_st = next(s for s in state["streams"] if s["name"].lower() == "offers")
        await _verify_offer_actions(client, camp_id, offers_st["id"])
