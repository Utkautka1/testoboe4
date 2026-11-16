"""
Модуль переиспользуемых колонок и аннотаций SQLAlchemy.

Определяет типы intpk, created_at, updated_at и строковые алиасы
для соблюдения принципа DRY при описании моделей.
"""

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, text
from sqlalchemy.orm import mapped_column

# Первичный целочисленный ключ
intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]

# Метка времени создания записи с часовым поясом
created_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('Europe/Moscow', NOW())"),
    ),
]

# Метка времени обновления записи
updated_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('Europe/Moscow', NOW())"),
        onupdate=text("TIMEZONE('Europe/Moscow', NOW())"),
    ),
]

# Стандартные ограничения строк
str_32 = Annotated[str, mapped_column(nullable=False)]
str_140 = Annotated[str, mapped_column(nullable=False)]
str_255 = Annotated[str, mapped_column(nullable=False)]
