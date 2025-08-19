import argparse
import logging
from os import PathLike
import shutil
import uuid
from enum import Enum
from pathlib import Path
from typing import Literal
from datetime import datetime

from fedot.api.builder import FedotBuilder
from fedot.core.repository.metrics_repository import (
    ClassificationMetricsEnum,
    RegressionMetricsEnum,
)
from fedot.core.pipelines.pipeline import Pipeline

from src.core.dataloaders import load_fedot_train_data_from_csv
from src.core.logger import LoggerFactory
from src.utils import read_yaml, write_yaml

TRAIN_LOGGER = LoggerFactory.get_logger("Train")


class TargetTrainMetricEnum(Enum):
    """Имя целевых метрик для определения лучшей модели"""

    classification = "roc_auc"
    regression = "mape"


class AvailableMetricsEnum(Enum):
    """Список всех допустимых метрик для задачи"""

    classification = list(metric.value for metric in ClassificationMetricsEnum)
    regression = list(metric.value for metric in RegressionMetricsEnum)


class AutoMLTrainer:
    """Класс для автоматического обучения моделей AutoML"""

    def _train_model(
        self,
        data_path: PathLike,
        task: str | Literal["classification", "regression"],
        target_columns: str | list[str | int],
        index_col: str | None = None,
        timeout: float = 5,
        task_id: str | None = None,
    ):
        """
        Функция обучения моделей AutoML

        Args:
            data_path (PathLike): Путь до .csv файла с данными
            task (str): Тип прогнозируемой задачи - 'classification' или 'regression'
            target_columns (str | list[str | int]): Целевые столбцы в данных, которые требуется предсказать
            index_col (str, optional): Колонка индекса в базе данных (будет отброшена при обучении)
            timeout (str): Максимально допустимое время (в минутах) для поиска оптимального решения
            task_id (str, optional): Имя задачи

        Returns:
            (dict[str, any]): Словарь с информацией о модели и её метриках
        """
        available_tasks = set(metric.name for metric in TargetTrainMetricEnum)
        if task not in available_tasks:
            raise ValueError(f"'task' must be {available_tasks}, got {task}")
        task_id = task_id or str(uuid.uuid4())[:8]

        # Выберем метрики
        target_metric = TargetTrainMetricEnum[task].value
        test_metrics = AvailableMetricsEnum[task].value

        # Загрузим данные
        train_data, test_data = load_fedot_train_data_from_csv(
            data_path, task, target_columns=target_columns, index_col=index_col
        )

        # Создадим модель
        model = (
            FedotBuilder(problem=task)
            .setup_composition(timeout=timeout, preset="auto", with_tuning=True)
            .setup_pipeline_evaluation(metric=target_metric, cv_folds=3)
            .setup_data_preprocessing(use_auto_preprocessing=True)
            .setup_output(
                logging_level=logging.ERROR, show_progress=False, keep_history=False
            )
            .build()
        )
        # Обучим модель
        TRAIN_LOGGER.info(
            f"<{task_id}> Start train model from '{data_path}' "
            f"by {len(train_data.target)+len(test_data.target)} samples"  # type: ignore
        )
        model.fit(features=train_data)

        # Получим метрики
        model.predict(test_data)
        model_metrics = model.get_metrics(metric_names=test_metrics)
        TRAIN_LOGGER.info(
            f"<{task_id}> Finish train model "
            f"with pipeline {model.current_pipeline.graph_description} "  # type: ignore
            f"and metrics {model_metrics}"
        )

        return model, model_metrics

    @staticmethod
    def _compare_metrics(first: dict[str, float], second: dict[str, float]) -> bool:
        """
        Сравнение метрик `first` и `second`

        Returns:
            (bool): лучше ли первый набор метрик, чем второй
        """
        if "mse" in first:
            return first["mse"] < second["mse"]
        elif "roc_auc" in first:
            return first["roc_auc"] > second["roc_auc"]
        else:
            raise RuntimeError(f"Metrics dictionary must contain 'mse' or 'roc_auc'")

    def train(
        self,
        data_path: PathLike,
        task: str | Literal["classification", "regression"],
        target_columns: str | list[str | int],
        save_model_path: PathLike,
        index_col: str | None = None,
        timeout: float = 5,
        if_exist: Literal["best", "last"] = "best",
    ):
        """
        Функция обучения моделей AutoML

        Args:
            data_path (PathLike): Путь до .csv файла с данными
            task (str): Тип прогнозируемой задачи - 'classification' или 'regression'
            target_columns (str | list[str | int]): Целевые столбцы в данных, которые требуется предсказать
            save_model_path (PathLike): Путь для сохранения весов моделей
            index_col (str, optional): Колонка индекса в базе данных (будет отброшена при обучении)
            timeout (str): Максимально допустимое время (в минутах) для поиска оптимального решения
            if_exist (str): Поведение при существовании модели в save_model_path:
                - 'best': сохраняется лучшая;
                - 'last': сохраняется более новая

        Returns:
            (dict[str, any]): Словарь с информацией о модели и её метриках
        """
        save_model_path = Path(save_model_path)
        task_id = str(uuid.uuid4())[:8]
        # Загрузим метрики старой модели (если есть)
        old_metrics_path = Path(save_model_path, "metrics.yaml")
        old_metrics = None
        if old_metrics_path.exists():
            old_metrics = read_yaml(old_metrics_path)

        # Обучим модель
        model, new_metrics = self._train_model(
            data_path=data_path,
            task=task,
            target_columns=target_columns,
            index_col=index_col,
            timeout=timeout,
            task_id=task_id,
        )
        # Избавимся от скаляров
        new_metrics = {name: float(m) for name, m in new_metrics.items()}
        # Получим pipeline модели
        model_pipeline: Pipeline = model.current_pipeline  # type: ignore

        # Сравним метрики
        save_new_model_flag = True
        if if_exist == "best" and old_metrics is not None:
            save_new_model_flag = self._compare_metrics(new_metrics, old_metrics)
        # Сохраним модель
        is_new_model_saving = False
        is_old_model_exist = save_model_path.exists()
        if save_new_model_flag:
            # Сохраним модели
            save_model_path.parent.mkdir(exist_ok=True, parents=True)
            cashed_model_path = save_model_path.with_name("_" + save_model_path.name)
            if is_old_model_exist:
                shutil.move(save_model_path, cashed_model_path)
            try:
                # Сохраним модель
                model_pipeline.save(str(save_model_path), create_subdir=False)
                # Сохраним метрики
                write_yaml(new_metrics, Path(save_model_path, "metrics.yaml"))
                is_new_model_saving = True
                TRAIN_LOGGER.info(
                    f"<{task_id}> Successfully save train model to {save_model_path}"
                )
            except Exception as e:
                if is_old_model_exist:
                    shutil.move(cashed_model_path, save_model_path)
                TRAIN_LOGGER.info(f"Save train model from to {save_model_path} aborted")
                raise
            finally:
                shutil.rmtree(cashed_model_path, ignore_errors=True)

        return {
            "pipeline": model_pipeline.graph_description,
            "metrics": new_metrics,
            "save": is_new_model_saving,
        }


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_root", type=str, help="Root path to dataset with 'config.yaml' file"
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        help="The maximum allowed time (in minutes) to find the optimal solution",
        default=5,
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

    # Считаем конфигурацию датасета
    data_root = Path(opt["data_root"])
    data_config_path = Path(data_root, "config.yaml")
    if not data_config_path.exists():
        raise FileNotFoundError(f"Not found 'config.yaml' file by path {data_root}")
    data_config = read_yaml(data_config_path)

    # Получим путь до данных
    data_path = Path(data_root, data_config["train_dataset"])
    # Сформируем путь сохранения модели
    model_name = (
        opt["save_name"]
        or f"{data_root.name}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"
    )
    save_model_path = Path(opt["save_dir"], model_name)

    # Обучим модель
    task = data_config["task"]
    trainer = AutoMLTrainer()
    model_info = trainer.train(
        data_path=data_path,
        task=task,
        target_columns=data_config["target_columns"],
        index_col=data_config.get("index_col"),
        save_model_path=save_model_path,
        timeout=opt.get("timeout", 5),
    )
