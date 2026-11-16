"""
Модуль перечислений (Enum) для моделей базы данных.

Содержит статусы кампаний и типов потоков трекера.
"""

from enum import Enum


class CampaignState(str, Enum):
    """Статусы кампании в трекере."""
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


class StreamType(str, Enum):
    """Типы потоков кампании."""
    REGULAR = "regular"
    FORCED = "forced"
    DEFAULT = "default"
