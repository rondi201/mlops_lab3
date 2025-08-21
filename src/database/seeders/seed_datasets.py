import json
from os import PathLike
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Dataset, PredictTask
from src.database.repository import ModelRepository


async def seed_datasets(config_path: str | PathLike, session: AsyncSession):
    """
    Актуализация данных Datasets на основе заданной конфигурации

    Args:
        config_path (str | PathLike): Путь до файла конфигурации в формате json, содержащего необходимые
            данные для обновления
        session (AsyncSession): Сессия к базе данных
    """
    # Загрузим конфигурацию заполнения из файла
    with open(config_path) as file:
        config: dict[str, Any] = json.load(file)

    # Получим данные для вставки
    source_models = [
        Dataset(
            # Оставим только те параметры, которые пренадлежат сущности
            **{k: v for k, v in data.items() if hasattr(Dataset, k)}
        )
        for data in config["data"]
    ]

    # Создадим репозиторий для работы с моделью типа предсказания
    task_repo = ModelRepository(model=PredictTask, session=session)
    # Создадим репозиторий для работы с моделью набора данных
    dataset_repo = ModelRepository(model=Dataset, session=session)

    # Подгрузим информацию об id типа предсказания
    for model, data in zip(source_models, config["data"]):
        if model.task_id is None:
            # Получим все tasks с нужным именем (имя уникально -> 0 или 1 запись)
            task_name = data["task_name"]
            task_ids = await task_repo.get_all(PredictTask.name == task_name)
            if task_ids:
                model.task_id = task_ids[0].id
            else:
                raise RuntimeError(f"No found PredictTask with name '{task_name}'")
    # Получим id набора данных для обновления, если он уже есть в базе
    for model in source_models:
        if model.id is None:
            # Получим все Datasets с нужным именем (имя уникально -> 0 или 1 запись)
            model_ids = await dataset_repo.get_all(Dataset.name == model.name)
            if model_ids:
                model.id = model_ids[0].id

    # Обновим или создадим данные
    for model in source_models:
        await dataset_repo.update(model)
