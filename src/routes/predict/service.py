from typing import Any
from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import UploadFile

from src.core.predict import predict, prepare_data_for_predict
from src.config import config_manager
from ...database.models import MLModel

# Создадим псевдоним типа, чтобы не тянуть зависимости из внешних файлов
AutoMLInputData = Any


class PredictService:
    @staticmethod
    def _get_model_path(ml_model: MLModel) -> Path:
        # Получим путь до сохранённой модели
        weights_root = config_manager.storage_config.weights_root
        model_path = Path(weights_root, ml_model.name)
        # Если нет весов для модели - сообщим об ошибке
        if not model_path.exists():
            raise FileNotFoundError(
                f"No found trained model '{ml_model.name}' by path {model_path}"
            )
        return model_path

    @staticmethod
    def load_data_from_file(data_file: UploadFile) -> pd.DataFrame:
        """
        Загрузка табличных данных из файла

        Args:
            data_file (file): Файл формата .csv

        Returns:
            (pd.DataFrame) Таблица данных

        Raises:
            ValueError: Если не удалось загрузить файл
        """
        data = pd.read_csv(data_file.file)

        if data.empty:
            raise ValueError(
                "Uploaded data file is empty. Check file format or correctness of the content."
            )

        return data

    @classmethod
    def prepare_data_for_prediction(
        cls,
        data: pd.DataFrame,
        ml_model: MLModel,
    ) -> AutoMLInputData:
        """
        Предобработка `data` данных из `dataset_name` набора данных

        Args:
            data (pd.DataFrame): Таблица с данными для предсказания
            ml_model (MLModel): Сущность ML модели

        Returns:
            (AutoMLInputData): Преобразованные в нужный формат данные

        Raises:
            (ValueError): Если входные данные невозможно преобразовать
        """
        # Получим путь до сохранённой модели
        model_path = cls._get_model_path(ml_model=ml_model)

        # Подготовим входные данные
        prepared_data = prepare_data_for_predict(
            data,
            task=ml_model.dataset.task.name,
            weight_path=model_path,
        )

        return prepared_data

    @classmethod
    def get_predict(
        cls,
        data: pd.DataFrame | AutoMLInputData,
        ml_model: MLModel,
    ) -> np.ndarray:
        """
        Получение предсказания на основе `data` данных с помощью `ml_model` модели

        Args:
            data (pd.DataFrame): Таблица с данными для предсказания
            ml_model (MLModel): Сущность ML модели

        Returns:
            (np.ndarray[N]): Массив предсказанных значений для каждой строки из `data`
        """

        # Получим путь до сохранённой модели
        model_path = cls._get_model_path(ml_model=ml_model)

        # Сделаем предсказание
        result = predict(data, task=ml_model.dataset.task.name, weight_path=model_path)
        return result
