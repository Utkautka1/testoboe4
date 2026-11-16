"""
Модуль централизованной настройки логирования приложения.

Предоставляет фабрику логгеров get_logger с форматированием,
выводом в консоль и ротацией в директорию logs/.
"""

import logging
import os
import sys

# Директория для логов
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Формат логов
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_handlers(logger: logging.Logger, name: str) -> None:
    """Настраивает консольный и файловый обработчики логгера."""
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_path = os.path.join(LOGS_DIR, f"{name}.log")
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Создает и конфигурирует логгер для заданной подсистемы."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    configure_handlers(logger, name)
    return logger
