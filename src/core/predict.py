import argparse
import uuid
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fedot.api.main import Fedot, InputData, MultiModalData

from src.core.logger import LoggerFactory

PREDICT_LOGGER = LoggerFactory.get_logger("Predict")


def prepare_data_for_predict(
    data: pd.DataFrame,
    task: str | Literal["classification", "regression"],
    weight_path: str | Path,
) -> InputData | MultiModalData:
    """
    Функция подготовки данных для предсказания моделью AutoML. Служит для предобработки данных вне
    контекста predict с целью выявления ошибок в данных

    Args:
        data (pd.DataFrame | InputData | MultiModalData): Таблица с данными для предсказания или
        task (str): Тип прогнозируемой задачи - 'classification' или 'regression'
        weight_path (str | list[str]): Путь до весов модели, используемой для предсказания.
            Модель должна быть обучена на том же наборе данных, откуда и `data`

    Returns:
        (np.ndarray[N]): Массив предсказанных значений для каждой строки из data
    """
    # Загрузим модель вместе с pipeline
    model = Fedot(task)
    model.load(weight_path)
    # Предобработаем данные
    try:
        prepared_data = model.data_processor.define_data(
            target=model.target, features=data, is_predict=True
        )
    except Exception as e:
        raise ValueError(
            f"The passed data cannot be preprocessed for prediction. Check the correctness"
            "of the passed data and whether it belongs to the training dataset."
        ).with_traceback(e.__traceback__)

    return prepared_data


def predict(
    data: pd.DataFrame | InputData | MultiModalData,
    task: str | Literal["classification", "regression"],
    weight_path: str | Path,
) -> np.ndarray:
    """
    Функция предсказания для модели AutoML

    Args:
        data (pd.DataFrame | InputData | MultiModalData): Данные для предсказания в виде таблице или подготовленные с помощью `prepare_data_for_predict`
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
    PREDICT_LOGGER.debug(f"<{predict_task_id}> Load model from '{weight_path}'")
    # Сделаем предсказание
    pred_values = model.predict(data)
    PREDICT_LOGGER.debug(
        f"<{predict_task_id}> Successfully predict '{len(pred_values)}' values"
    )
    return pred_values


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=str, help="Type of prediction task")
    parser.add_argument(
        "-d",
        "--data-file",
        type=str,
        help="Path to .csv file for prediction",
        required=True,
    )
    parser.add_argument(
        "-w", "--weight_path", type=str, help="Path to model weights", required=True
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        help="save result model weights root dir",
        default="runs",
    )
    parser.add_argument(
        "--save-name", type=str, help="save result model weights name", default=None
    )

    return parser.parse_args()


if __name__ == "__main__":
    opt = vars(parse_opt())

    # Считаем файл данных
    data = pd.read_csv(opt["data_file"])

    predictions = predict(
        data=data,
        task=opt["task"],
        weight_path=opt["weight_path"],
    )

    print("Model prediction is:")
    print(predictions)
