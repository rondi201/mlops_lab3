from urllib.parse import urlencode
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)


class DatabaseSessionBuilder:
    def __init__(
        self,
        dialect: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ):
        """
        Инициализация инструмента работы с базой данных

        Args:
            dialect (str): Вид диалекта SQL (см. https://docs.sqlalchemy.org/en/20/core/engines.html)
            host (str): Адрес базы данных
            port (int): Порт базы данных
            user (str): Логин для доступа к базе данных
            password (str): Пароль для доступа к базе данных
            database (str): Имя базы данных
        """
        url = f"{dialect}://{user}:{password}@{host}:{port}/{database}"
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            pool_pre_ping=True,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            # autoflush=False,
            # autocommit=False,
            # expire_on_commit=False,
        )

    @staticmethod
    def build_link(
        dialect: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        **url_params,
    ) -> str:
        """
        Формирование ссылки к базе данных

        Args:
            dialect (str): Вид диалекта SQL (см. https://docs.sqlalchemy.org/en/20/core/engines.html)
            host (str): Адрес базы данных
            port (int): Порт базы данных
            user (str): Логин для доступа к базе данных
            password (str): Пароль для доступа к базе данных
            database (str): Имя базы данных

        Return:
            (str): Ссылка для полуения доступа к базе данных в формате URL. Формируется на основе шаблона вида:
                "{dialect}://{user}:{password}@{host}:{port}/{database}?{url_params}"
        """
        url = f"{dialect}://{user}:{password}@{host}:{port}/{database}"
        if url_params:
            url = url + "?" + urlencode(url_params)
        return url

    async def dispose(self) -> None:
        """Завершение работы с базой данных"""
        await self.engine.dispose()

    def get_session(self) -> Session:
        """Получение синхронной сессии к базе данных"""
        return self.session_factory().sync_session

    def get_async_session(self) -> AsyncSession:
        """Получение асинхронной сессии к базе данных"""
        return self.session_factory()
