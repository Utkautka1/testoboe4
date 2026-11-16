"""
Модуль асинхронного подключения к базе данных PostgreSQL.

Инициализирует асинхронный движок SQLAlchemy с пулом соединений
и фабрику асинхронных сессий.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings
from core.logger import get_logger

log = get_logger("psql")

# Создание асинхронного движка
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый декларативный класс для моделей SQLAlchemy."""
    pass


@asynccontextmanager
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для работы с сессией БД.

    Гарантирует закрытие сессии и откат при возникновении ошибок.
    """
    session = async_session_maker()
    try:
        yield session
    except Exception as exc:
        log.error(f"Ошибка в транзакции БД: {exc}")
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency для инжекции сессии базы данных в роуты.
    """
    async with async_db_session() as session:
        yield session
