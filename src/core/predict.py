import uuid
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fedot.api.main import Fedot

from src.core.logger import LoggerFactory

PREDICT_LOGGER = LoggerFactory.get_logger("Predict")


def predict(
    data: pd.DataFrame,
    task: str | Literal["classification", "regression"],
    weight_path: str | Path,
) -> np.ndarray:
    """
    Функция предсказания для модели AutoML

    Args:
        data (pd.DataFrame): Таблица с данными для предсказания
        task (str): Тип прогнозируемой задачи - 'classification' или 'regression'
        weight_path (str | list[str]): Путь до весов модели, используемой для предсказания.
            Модель должна быть обучена на том же наборе данных, откуда и `data`

    Returns:
        (np.ndarray[N]): Массив предсказанных значений для каждой строки из data
    """
    predict_task_id = str(uuid.uuid4())[:8]

    # Загрузим модель
    model = Fedot(task)
    model.load(weight_path)
    PREDICT_LOGGER.info(f"<{predict_task_id}> Load model from '{weight_path}'")
    # Сделаем предсказание
    pred_values = model.predict(data)
    PREDICT_LOGGER.info(
        f"<{predict_task_id}> Successfully predict '{len(pred_values)}' values"
    )
    return pred_values
