"""
Модульные тесты для алгоритмов расчета долей офферов и генерации alias.

Проверяет функции разбиения долей с пинами (calculate_pinned_shares)
и генерацию уникального alias кампании.
"""

import pytest
from services.creator_service import build_alias
from services.shares_calculator import calculate_pinned_shares


def test_calculate_pinned_shares_equal():
    """Проверка равного распределения долей между двумя офферами."""
    offers = [
        {"id": 1, "status": "active", "is_pinned": False, "share": 0},
        {"id": 2, "status": "active", "is_pinned": False, "share": 0},
    ]
    res = calculate_pinned_shares(offers)
    assert [o["share"] for o in res] == [50, 50]


def test_calculate_pinned_shares_with_pinned():
    """Проверка сохранения доли у закрепленного (pinned) оффера."""
    offers = [
        {"id": 1, "status": "active", "is_pinned": True, "share": 25},
        {"id": 2, "status": "active", "is_pinned": False, "share": 0},
        {"id": 3, "status": "active", "is_pinned": False, "share": 0},
    ]
    res = calculate_pinned_shares(offers)
    assert res[0]["share"] == 25
    assert res[1]["share"] == 38
    assert res[2]["share"] == 37
    assert sum(o["share"] for o in res) == 100


def test_calculate_pinned_shares_removed_zero():
    """Проверка, что удаленный оффер получает share = 0."""
    offers = [
        {"id": 1, "status": "removed", "is_pinned": False, "share": 50},
        {"id": 2, "status": "active", "is_pinned": False, "share": 0},
    ]
    res = calculate_pinned_shares(offers)
    assert res[0]["share"] == 0
    assert res[1]["share"] == 100


def test_build_alias():
    """Проверка генерации алиаса кампании."""
    alias = build_alias("test_strygin_demo")
    assert "test-strygin-demo" in alias
    assert len(alias) > len("test-strygin-demo")
