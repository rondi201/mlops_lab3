"""
Модуль создания и внедрения зависимостей.

Ввиду того что зависимости могут быть вложенными, то обёртка всех зависимостей в единый класс затруднительна.
Поэтому реализация зависимостей представлена в функциональном виде. Чтобы избежать инициализации глобальных
переменных, таких как объекты базы данных, все инициализации спрятаны внуть кешированных функций.
"""

from functools import cache
from logging import Logger
from typing import AsyncGenerator

from fastapi import Depends

from src.database.session import DatabaseSessionBuilder, AsyncSession
from src.database.repository import DatabaseRepository
from src.config import config_manager
from src.core.logger import LoggerFactory


@cache
def get_database_session_builder() -> DatabaseSessionBuilder:
    """Получение создателя сессий к базе данных"""
    db_config = config_manager.db_config
    return DatabaseSessionBuilder(
        dialect=db_config.dialect,
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password.get_secret_value(),
        database=db_config.database,
    )


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение асинхронной сессии к базе данных"""
    async with get_database_session_builder().get_async_session() as session:
        yield session


async def get_database_repository(
    session: AsyncSession = Depends(get_database_session),
) -> DatabaseRepository:
    """Получение репозитория для работы с базой данных"""
    return DatabaseRepository(session)


async def get_app_logger() -> Logger:
    """Получение логгера для логирования сообщений"""
    return LoggerFactory.get_logger("APP")
