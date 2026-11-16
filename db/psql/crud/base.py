"""
Базовый класс операций манипуляции моделями (ModelAdmin).

Предоставляет переиспользуемые CRUD-методы для моделей SQLAlchemy.
"""

from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from core.psql import async_db_session

ModelType = TypeVar("ModelType")


class ModelAdmin(Generic[ModelType]):
    """Миксин с универсальными CRUD-методами для моделей."""

    @classmethod
    async def get_by_id(cls: Type[ModelType], item_id: int) -> Optional[ModelType]:
        """
        Получает запись по первичному ключу.
        """
        async with async_db_session() as session:
            stmt = select(cls).where(getattr(cls, "id") == item_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def get_all(cls: Type[ModelType], limit: int = 100) -> List[ModelType]:
        """
        Получает список всех записей с ограничением количества.
        """
        async with async_db_session() as session:
            stmt = select(cls).order_by(getattr(cls, "id").desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def create(cls: Type[ModelType], **kwargs: Any) -> ModelType:
        """
        Создает и сохраняет новую запись в БД.
        """
        async with async_db_session() as session:
            instance = cls(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance
