import uuid
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fedot.api.main import Fedot

from src.logger import LoggerFactory

TRAIN_LOGGER = LoggerFactory.get_logger('Predict')


def predict(
        data: pd.DataFrame,
        task: Literal['classification', 'regression'],
        weight_path: str | Path,
) -> np.ndarray:
    predict_task_id = str(uuid.uuid4())[:8]

    # Загрузим модель
    model = Fedot(task)
    model.load(weight_path)
    TRAIN_LOGGER.info(
        f"<{predict_task_id}> Load model from '{weight_path}'"
    )
    # Сделаем предсказание
    pred_values = model.predict(data)
    TRAIN_LOGGER.info(
        f"<{predict_task_id}> Successfully predict '{len(pred_values)}' values"
    )
    return pred_values
