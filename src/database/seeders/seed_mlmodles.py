import datetime
import json
from os import PathLike
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Dataset, MLModel
from src.database.repository import ModelRepository
from src.config import config_manager


async def seed_mlmodels(config_path: str | PathLike, session: AsyncSession):
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

    # Проверим наличие данных для переданных сущностей
    for row in config["data"]:
        # Получим путь до сохранённой модели
        weights_root = config_manager.storage_config.weights_root
        name = row["name"]
        model_path = Path(weights_root, name)
        # Проверим, что он существует
        if not model_path.exists():
            raise RuntimeError(
                f"No found weights for mlmodel with name '{name}' by path '{model_path}'"
            )

    # Преобразуем данные в нужные типы
    for field_name, deserializer in (("trained_at", datetime.datetime.fromisoformat),):
        for row in config["data"]:
            row[field_name] = deserializer(row[field_name])
    # Получим данные для вставки
    source_models = [
        MLModel(
            # Оставим только те параметры, которые пренадлежат сущности
            **{k: v for k, v in data.items() if hasattr(MLModel, k)}
        )
        for data in config["data"]
    ]

    # Создадим репозиторий для работы с моделью типа предсказания
    dataset_repo = ModelRepository(model=Dataset, session=session)
    # Создадим репозиторий для работы с моделью набора данных
    mlmodel_repo = ModelRepository(model=MLModel, session=session)

    # Подгрузим информацию об id базы данных
    for model, data in zip(source_models, config["data"]):
        if model.dataset_id is None:
            # Получим все datasets с нужным именем (имя уникально -> 0 или 1 запись)
            dataset_name = data["dataset_name"]
            dataset_ids = await dataset_repo.get_all(Dataset.name == dataset_name)
            if dataset_ids:
                model.dataset_id = dataset_ids[0].id
            else:
                raise RuntimeError(f"No found Dataset with name '{dataset_name}'")
    # Получим id ml моделей для обновления, если он уже есть в базе
    for model in source_models:
        if model.id is None:
            # Получим все MLModel с нужным именем (имя уникально -> 0 или 1 запись)
            model_ids = await mlmodel_repo.get_all(MLModel.name == model.name)
            if model_ids:
                model.id = model_ids[0].id

    # Обновим или создадим данные
    for model in source_models:
        await mlmodel_repo.update(model)
