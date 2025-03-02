import argparse
import logging
import shutil
import uuid
from enum import Enum
from pathlib import Path
from typing import Literal
from datetime import datetime

from fedot.api.builder import FedotBuilder
from fedot.core.repository.metrics_repository import ClassificationMetricsEnum, RegressionMetricsEnum

from src.dataloaders import load_csv_train_data
from src.logger import LoggerFactory
from src.utils import read_yaml, write_yaml

TRAIN_LOGGER = LoggerFactory.get_logger('Train')


class TargetTrainMetricEnum(Enum):
    classification = 'roc_auc'
    regression = 'mape'


class AvailableMetricsEnum(Enum):
    classification = (metric.value for metric in ClassificationMetricsEnum)
    regression = (metric.value for metric in RegressionMetricsEnum)


def train(
        data_path: str | Path,
        task: Literal['classification', 'regression'],
        target_columns: str | list[str],
        save_model_path: str | Path,
        index_col: str | None = None,
        timeout: float = 5,
):
    """
    Функция обучения моделей AutoML

    Args:
        data_path (str | Path): Путь до .csv файла с данными
        task (str): Тип прогнозируемой задачи - 'classification' или 'regression'
        target_columns (str | list[str]): Целевые столбцы в данных, которые требуется предсказать
        save_model_path (str | Path): Путь для сохранения весов моделей
        index_col (str, optional): Колонка индекса в базе данных (будет отброшена при обучении)
        timeout (str): Максимально допустимое время (в минутах) для поиска оптимального решения

    Returns:
        (dict[str, any]): Словарь с информацией о модели и её метриках
    """
    available_tasks = set(metric.name for metric in TargetTrainMetricEnum)
    if task not in available_tasks:
        raise ValueError(f"'task' must be {available_tasks}, got {task}")
    train_task_id = str(uuid.uuid4())[:8]

    # Выберем метрики
    target_metric = TargetTrainMetricEnum[task].value
    test_metrics = AvailableMetricsEnum[task].value

    # Загрузим данные
    train_data, test_data = load_csv_train_data(data_path, task, target_columns=target_columns, index_col=index_col)

    # Создадим модель
    model = (FedotBuilder(problem=task)
             .setup_composition(timeout=timeout, preset='auto', with_tuning=True)
             .setup_pipeline_evaluation(metric=target_metric, cv_folds=3)
             .setup_data_preprocessing(use_auto_preprocessing=True)
             .setup_output(logging_level=logging.ERROR, show_progress=False, keep_history=False)
             .build())
    # Обучим модель
    TRAIN_LOGGER.info(
        f"<{train_task_id}> Start train model from '{data_path}' "
        f"by {len(train_data.target)+len(test_data.target)} samples"
    )
    model.fit(features=train_data)

    # Получим метрики
    model.predict(test_data)
    model_metrics = model.get_metrics(
        metric_names=test_metrics
    )
    TRAIN_LOGGER.info(
        f"<{train_task_id}> Finish train model "
        f"with pipeline {model.current_pipeline.graph_description} "
        f"and metrics {model_metrics}"
    )
    # Сохраним модель
    model.current_pipeline.save(save_model_path, create_subdir=False)
    TRAIN_LOGGER.info(
        f"<{train_task_id}> Successfully save train model to {save_model_path}"
    )

    return {
        "pipeline": model.current_pipeline.graph_description,
        "metrics": {name: float(m) for name, m in model_metrics.items()}
    }


def compare_metrics(first: dict[str], second: dict[str]) -> bool:
    """
    Сравнение метрик `first` и `second`

    Returns:
        (bool): лучше ли первый набор метрик, чем второй
    """
    if 'mse' in first:
        return first['mse'] < second['mse']
    elif 'roc_auc' in first:
        return first['roc_auc'] > second['roc_auc']
    else:
        raise RuntimeError(f"Metrics dictionary must contain 'mse' or 'roc_auc'")


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_root', type=str,
                        help="Root path to dataset with 'config.yaml' file")
    parser.add_argument('-t', '--timeout', type=float,
                        help='The maximum allowed time (in minutes) to find the optimal solution', default=5)
    parser.add_argument('--save-dir', type=str, help='save result model weights root dir', default='runs')
    parser.add_argument('--save-name', type=str, help='save result model weights name', default=None)

    return parser.parse_args()


if __name__ == "__main__":
    opt = vars(parse_opt())

    # Считаем конфигурацию датасета
    data_root = Path(opt['data_root'])
    data_config_path = Path(data_root, 'config.yaml')
    if not data_config_path.exists():
        raise FileNotFoundError(f"Not found 'config.yaml' file by path {data_root}")
    data_config = read_yaml(data_config_path)

    # Получим путь до данных
    data_path = Path(data_root, data_config['train_dataset'])
    # Сформируем путь сохранения модели
    model_name = opt['save_name'] or f"{data_root.name}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
    save_model_path = Path(opt['save_dir'], model_name)
    # Сформируем путь для временного сохранения модели
    cashed_model_path = Path(opt['save_dir'], model_name + '_pipeline')
    # Загрузим метрики старой модели
    old_metrics_path = Path(save_model_path, 'metrics.yaml')
    old_metrics = None
    if old_metrics_path.exists():
        old_metrics = read_yaml(old_metrics_path)

    # Обучим модель
    task = data_config['task']
    try:
        model_info = train(
            data_path=data_path,
            task=task,
            target_columns=data_config['target_columns'],
            index_col=data_config.get('index_col'),
            save_model_path=cashed_model_path,
            timeout=opt.get('timeout', 5)
        )

        # Сравним метрики
        new_metrics = model_info['metrics']
        save_new_model_flag = True
        if old_metrics is not None:
            save_new_model_flag = compare_metrics(new_metrics, old_metrics)
        # Сохраним модель
        if save_new_model_flag:
            shutil.rmtree(save_model_path, ignore_errors=True)
            shutil.move(cashed_model_path, save_model_path)
            # Сохраним метрики
            write_yaml(new_metrics, Path(save_model_path, 'metrics.yaml'))
            TRAIN_LOGGER.info(
                f"Resave train model from {cashed_model_path} to {save_model_path}"
            )
    finally:
        shutil.rmtree(cashed_model_path, ignore_errors=True)
