from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI


from . import dependencies
from .routes.router import router as api_router
from .core.logger import LoggerFactory
from .config import config_manager
from .database.repository import DatabaseRepository

app_logger = LoggerFactory.get_logger("APP")


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    try:
        # Проверим подключчение к базе данных
        async with dependencies.get_database_session_builder().get_async_session() as session:
            await DatabaseRepository(session).ping()
        yield
    finally:
        # Остановка приложения
        pass


app = FastAPI(openapi_url="/api/v1/openapi.json", lifespan=lifespan)
app.include_router(api_router, prefix=config_manager.api_config.prefix)


if __name__ == "__main__":
    uvicorn.run(
        f"{__name__}:app",
        host=config_manager.run_config.host,
        port=config_manager.run_config.port,
        log_level="info",
    )
