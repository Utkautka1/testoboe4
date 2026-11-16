"""
Точка входа FastAPI приложения для сервиса управления кампаниями Keitaro.

Настраивает жизненный цикл (lifespan), подключает роутеры API,
раздает статические файлы и интерфейс SPA.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.router.campaigns import router as campaigns_router
from api.router.dictionaries import router as dictionaries_router
from core.logger import get_logger
from core.psql import Base, engine
from integrations.keitaro import keitaro_client

log = get_logger("api")


async def init_services() -> None:
    """Инициализирует подключение к базе данных и трекеру."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("Подключение к PostgreSQL и проверка схемы — OK")
    except Exception as exc:
        log.warning(f"Предупреждение подключения к БД: {exc}")

    try:
        if await keitaro_client.authenticate():
            log.info("Интеграция с Keitaro API активна")
    except Exception as exc:
        log.error(f"Не удалось подключиться к Keitaro: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управляет жизненным циклом приложения: проверка Keitaro и БД."""
    log.info("=" * 60)
    log.info("🚀 ЗАПУСК сервиса Keitaro Wrapper")
    log.info("=" * 60)

    await init_services()
    yield

    log.info("Остановка сервиса Keitaro Wrapper...")
    await keitaro_client.close()
    await engine.dispose()


app = FastAPI(
    title="Keitaro Wrapper API",
    description="Сервис создания кампаний и управления офферами трекера Keitaro",
    version="1.0.0",
    lifespan=lifespan,
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключение роутеров
app.include_router(campaigns_router)
app.include_router(dictionaries_router)


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Отображает главную страницу веб-интерфейса."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health_check():
    """Эндпоинт проверки жизнеспособности сервиса."""
    return {"status": "ok"}
