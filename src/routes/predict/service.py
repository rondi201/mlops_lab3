from pathlib import Path
import pandas as pd
import numpy as np
from fastapi import UploadFile

from src.core.predict import predict
from src.config import config_manager
from ...database.models import MLModel


class PredictService:
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

        return data

    @staticmethod
    def get_predict(
        data: pd.DataFrame,
        ml_model: MLModel,
    ) -> np.ndarray:
        """
        Получение предсказания на основе `data` данных из `dataset_name` набора данных

        Args:
            data (pd.DataFrame): Таблица с данными для предсказания
            ml_model (MLModel): Сущность ML модели

        Returns:
            (np.ndarray[N]): Массив предсказанных значений для каждой строки из data
        """

        # Получим путь до сохранённой модели
        weights_root = config_manager.storage_config.weights_root
        model_path = Path(weights_root, ml_model.name)
        # Если нет весов для модели - сообщим об ошибке
        if not model_path.exists():
            raise FileNotFoundError(
                f"No found trained model '{ml_model.name}' by path {model_path}"
            )
        # Сделаем предсказание
        result = predict(data, task=ml_model.dataset.task.name, weight_path=model_path)
        return result
