"""
Алгоритмы пересчета долей (весов) офферов в потоке кампании.

Поддерживают закрепленные (pinned) веса, исключение удаленных офферов (removed),
и автоматическое распределение остатка до 100%.
"""

from typing import Dict, List


def partition_offers_by_status(offers: List[Dict]) -> tuple[List[Dict], int]:
    """Разделяет офферы на активные незакрепленные и сумму закрепленных."""
    active_unpinned = []
    pinned_total = 0
    for off in offers:
        if off.get("status") == "removed":
            off["share"] = 0
        elif off.get("is_pinned"):
            pinned_total += off.get("share", 0)
        else:
            active_unpinned.append(off)
    return active_unpinned, pinned_total


def calculate_pinned_shares(offers: List[Dict]) -> List[Dict]:
    """Рассчитывает доли активных офферов с учетом закрепленных весов."""
    active_unpinned, pinned_total = partition_offers_by_status(offers)
    remaining_share = max(0, 100 - pinned_total)
    count = len(active_unpinned)

    if count > 0:
        base = remaining_share // count
        rem = remaining_share % count
        for i, off in enumerate(active_unpinned):
            off["share"] = base + (rem if i == 0 else 0)

    return offers
