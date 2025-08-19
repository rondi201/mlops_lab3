# import functools
# from pathlib import Path
# from typing import Any
# from dataclasses import asdict

# import numpy as np
# import pandas as pd

# from src.core.predict import predict
# from src.core.train import AutoMLTrainer
# from src.core.database import SQLDatabaseServer
# from src.utils import read_yaml
# from src.models import Dataset


# class APIMethods:
#     datasets_root: str | Path = None  # type: ignore
#     weights_root: str | Path = None  # type: ignore
#     database: SQLDatabaseServer = None  # type: ignore

#     @classmethod
#     def setting(
#             cls,
#             datasets_root: str | Path,
#             weights_root: str | Path,
#             database: SQLDatabaseServer,
#             **kwargs
#     ):
#         """
#         Настройка API

#         Args:
#             datasets_root (str | Path): Путь до папки с наборами данных
#             weights_root (str | Path): Путь до папки с весами предобученных моделей
#             database (SQLDatabaseServer): База данных для получение информации о наборах данных и моделей
#         """
#         cls.datasets_root = datasets_root
#         cls.weights_root = weights_root
#         cls.database = database

#     @staticmethod
#     def setting_validation_wrapper(
#             datasets_checking: bool = True,
#             weights_checking: bool = True,
#             database_checking: bool = True,
#     ):
#         """ Обёртка `classmethod` методов для проверки состояния класса перед вызовом """
#         def proxy(func):
#             @functools.wraps(func)  # Прокидывание названия и документации целевой функции
#             def wrapper(cls, *args, **kwargs):
#                 print(args)
#                 if datasets_checking and cls.datasets_root is None:
#                     raise RuntimeError(f"'datasets_root' must be set by APIMethods.setting()")
#                 if weights_checking and cls.weights_root is None:
#                     raise RuntimeError(f"'datasets_root' must be set by APIMethods.setting()")
#                 if database_checking and cls.database is None:
#                     raise RuntimeError(f"'database' must be set by APIMethods.setting()")

#                 return func(cls, *args, **kwargs)
#             return wrapper
#         return proxy

#     @classmethod
#     @setting_validation_wrapper()
#     def get_dataset_path(cls, name: str) -> Path:
#         """ Получение пути до наборов данных """
#         dataset_path = Path(cls.datasets_root, name)
#         if not dataset_path.exists():
#             raise FileNotFoundError(f"Dataset with the name '{name}' is not found")
#         return dataset_path

#     @classmethod
#     @setting_validation_wrapper()
#     def get_dataset_names(cls) -> list[str]:
#         """ Получение имён наборов данных """
#         return cls.database.get_dataset_names()

#     @classmethod
#     @setting_validation_wrapper()
#     def get_dataset_configs(cls) -> dict[str, Dataset]:
#         """
#         Получение конфигурация наборов данных

#         Returns:
#             (dict[str, Dataset]): Параметры наборов данных вида {<dataset_name>: <dataset_config>}
#         """
#         datasets = cls.database.get_datasets()
#         return {
#             data.name: data for data in datasets
#         }

#     @classmethod
#     @setting_validation_wrapper()
#     def get_dataset_config(cls, name: str) -> Dataset:
#         """
#         Получение конфигурация наборов данных

#         Args:
#             name (str): Имя набора данных

#         Returns:
#             (Dataset): Параметры набора данных
#         """
#         dataset = cls.database.get_dataset_by_name(name)
#         return dataset

#     @classmethod
#     @setting_validation_wrapper()
#     def get_model_metrics(cls, dataset_name: str) -> dict[str, Any] | None:
#         """
#         Получение метрик модели, обученной на `dataset_name` наборе данных или `None`, если модели не существует
#         """
#         # Загрузим метрики модели
#         metrics_path = Path(cls.weights_root, dataset_name, 'metrics.yaml')
#         metrics = None
#         if metrics_path.exists():
#             metrics = read_yaml(metrics_path)
#         return metrics

#     @classmethod
#     @setting_validation_wrapper()
#     def get_predict(
#             cls,
#             data: pd.DataFrame,
#             dataset_name: str,
#     ) -> np.ndarray:
#         """
#         Получение предсказания на основе `data` данных из `dataset_name` набора данных

#         Args:
#             data (pd.DataFrame): Таблица с данными для предсказания
#             dataset_name (str): Имя набора данных

#         Returns:
#             (np.ndarray[N]): Массив предсказанных значений для каждой строки из data
#         """
#         # Прочитаем конфигурацию предсказания
#         predict_config = cls.database.get_predict_info_by_dataset_name(dataset_name)
#         # Получим путь до сохранённой модели
#         model_path = Path(cls.weights_root, predict_config.model.name)
#         if not model_path.exists():
#             raise FileNotFoundError(f"No found trained model for '{dataset_name}' dataset by path {model_path}")
#         # Сделаем предсказание
#         result = predict(
#             data,
#             task=predict_config.dataset.task.name,
#             weight_path=model_path
#         )
#         return result

#     @classmethod
#     @setting_validation_wrapper()
#     def run_train(
#             cls,
#             dataset_name: str,
#             time_limit: float = 5,
#     ) -> dict[str, Any]:
#         """
#         Обучение модели на `dataset_name` наборе данных

#         Args:
#             dataset_name (str): Имя набора данных
#             time_limit (float): Максимально допустимое время (в минутах) для поиска оптимального решения

#         Returns:
#             (dict[str, any]): Словарь с информацией о модели и её метриках
#         """
#         # Получим путь до набора данных
#         data_path = cls.get_dataset_path(dataset_name)
#         # Прочитаем конфигурацию датасета
#         dataset_config: Dataset = cls.get_dataset_config(dataset_name)
#         # Сформируем путь для сохранения модели
#         save_model_path = Path(cls.weights_root, dataset_name)
#         # Запустим обучение
#         trainer = AutoMLTrainer()
#         model_info = trainer.train(
#             data_path=Path(data_path, 'test.csv'),
#             task=dataset_config.task.name,
#             target_columns=dataset_config.target_column,
#             index_col=dataset_config.index_column,
#             save_model_path=save_model_path,
#             timeout=time_limit,
#             if_exist='best'
#         )
#         model_info['pipeline']['nodes'] = [str(node) for node in model_info['pipeline']['nodes']]
#         return model_info
