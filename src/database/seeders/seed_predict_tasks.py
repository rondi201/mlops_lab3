import json
from os import PathLike

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import PredictTask
from src.database.repository import ModelRepository


async def seed_predict_tasks(config_path: str | PathLike, session: AsyncSession):
    """
    Актуализация read-only данных PredictTask на основе заданной конфигурации

    Args:
        config_path (str | PathLike): Путь до файла конфигурации в формате json, содержащего необходимые
            данные для обновления
        session (AsyncSession): Сессия к базе данных
    """
    # Загрузим конфигурацию заполнения из файла
    with open(config_path) as file:
        config = json.load(file)

    # Создадим репозиторий для работы с моделью
    model_repo = ModelRepository(model=PredictTask, session=session)

    # Получим данные для вставки
    source_models = [PredictTask(**data) for data in config["data"]]

    # Обновим или создадим данные
    for model in source_models:
        await model_repo.update(model)
