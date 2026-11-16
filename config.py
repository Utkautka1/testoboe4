"""
Модуль конфигурации приложения и параметров окружения.

Загружает настройки из переменных окружения и .env файла.
Определяет параметры подключения к БД PostgreSQL, настройки Keitaro API,
а также дефолтные значения сущностей (домен, группа, источник).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс настроек проекта с типизацией Pydantic Settings.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Настройки сервиса
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False

    # Префикс фамилии для тестовых кампаний
    CAMPAIGN_PREFIX: str = "test_strygin_"

    # Параметры подключения к PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/keitaro_wrapper"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Настройки интеграции с Keitaro
    KEITARO_BASE_URL: str = "https://tlgk.host"
    KEITARO_LOGIN: str = "fortests@etolegko.com"
    KEITARO_PASSWORD: str = "T9*2jiT8zoUKEH1J7VvFqkXM"
    KEITARO_API_KEY: str = ""

    # Дефолтные привязки Keitaro согласно ТЗ
    KEITARO_DEFAULT_DOMAIN_ID: int = 1813
    KEITARO_DEFAULT_GROUP_ID: int = 9799
    KEITARO_DEFAULT_SOURCE_ID: int = 836


settings = Settings()
