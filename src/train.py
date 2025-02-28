import logging
import uuid
from pathlib import Path
from typing import Literal

from fedot.api.builder import FedotBuilder

from src.dataloaders import load_csv_train_data
from src.logger import LoggerFactory

TRAIN_LOGGER = LoggerFactory.get_logger('Train')


def train(
        data_path: str | Path,
        task: Literal['classification', 'regression'],
        target_columns: str | list[str],
        save_model_path: str | Path,
        index_col: str | None = None,
        timeout: float = 5,
):
    train_task_id = str(uuid.uuid4())[:8]

    # Выберем метрики
    if task == 'regression':
        metric = ['mse', 'mae', 'mape']
    elif task == 'classification':
        metric = ['roc_auc', 'f1', 'accuracy']
    else:
        raise ValueError(f"'task' must be 'classification' or 'regression', got {task}")

    # Загрузим данные
    train_data, test_data = load_csv_train_data(data_path, task, target_columns=target_columns, index_col=index_col)

    # Создадим модель
    model = (FedotBuilder(problem=task)
             .setup_composition(timeout=timeout, preset='auto', with_tuning=True)
             .setup_pipeline_evaluation(metric=metric[0], cv_folds=3)
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
        metric_names=metric
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
        "metrics": model_metrics
    }
