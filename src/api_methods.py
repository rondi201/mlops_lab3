from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.predict import predict
from src.train import train
from src.utils import read_yaml


class APIMethods:
    datasets_root: str | Path = None
    weights_root: str | Path = None
    
    @classmethod
    def setting(
            cls,
            datasets_root: str | Path,
            weights_root: str | Path, 
            **kwargs
    ):
        """
        Настройка API
        
        Args:
            datasets_root (str | Path): Путь до папки с наборами данных
            weights_root (str | Path): Путь до папки с весами предобученных моделей
        """
        cls.datasets_root = datasets_root
        cls.weights_root = weights_root
    
    @classmethod
    def _check_settings(cls):
        if cls.datasets_root is None:
            raise RuntimeError(f"'datasets_root' must be set by APIMethods.setting()")
        if cls.weights_root is None:
            raise RuntimeError(f"'datasets_root' must be set by APIMethods.setting()")

    @classmethod
    def get_dataset_path(cls, name: str) -> Path:
        dataset_path = Path(cls.datasets_root, name)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset with the name '{name}' is not found")
        return dataset_path
    
    @classmethod
    def get_dataset_names(cls) -> list[str]:
        """ Получение имён наборов данных """
        cls._check_settings()
        datasets_root = Path(cls.datasets_root)
        dataset_names = []
        for dataset_path in datasets_root.iterdir():
            if Path(dataset_path, 'config.yaml').exists():
                dataset_names.append(dataset_path.name)
        return dataset_names

    @classmethod
    def get_dataset_configs(cls) -> dict[str, dict]:
        """
        Получение конфигурация наборов данных

        Returns:
            (dict[str, any]): Параметры наборов данных вида {<dataset_name>: <dataset_config>}
        """
        cls._check_settings()
        datasets_root = Path(cls.datasets_root)
        dataset_result = {}
        # Пройдёмся по всем доступным наборам данных
        for dataset_path in datasets_root.iterdir():
            config_path = Path(dataset_path, 'config.yaml')
            if not config_path.exists():
                continue
            # Получим конфигурацию
            dataset_result[dataset_path.name] = read_yaml(config_path)
        return dataset_result

    @classmethod
    def get_dataset_config(cls, name: str) -> dict[str, dict]:
        """
        Получение конфигурация наборов данных

        Args:
            name (str): Имя набора данных

        Returns:
            (dict[str, any]): Параметры набора данных
        """
        cls._check_settings()
        dataset_path = cls.get_dataset_path(name)
        config_path = Path(dataset_path, 'config.yaml')
        if not config_path.exists():
            raise FileNotFoundError(f"Config file '{config_path.name}' is not found in dataset '{dataset_path}'")
        config = read_yaml(config_path)
        return config

    @classmethod
    def get_model_metrics(cls, dataset_name: str) -> dict[str, Any] | None:
        """
        Получение метрик модели, обученной на `dataset_name` наборе данных или `None`, если модели не существует
        """
        # Загрузим метрики модели
        metrics_path = Path(cls.weights_root, dataset_name, 'metrics.yaml')
        metrics = None
        if metrics_path.exists():
            metrics = read_yaml(metrics_path)
        return metrics

    @classmethod
    def get_predict(
            cls,
            data: pd.DataFrame,
            dataset_name: str,
    ) -> np.ndarray:
        """
        Получение предсказания на основе `data` данных из `dataset_name` набора данных

        Args:
            data (pd.DataFrame): Таблица с данными для предсказания
            dataset_name (str): Имя набора данных

        Returns:
            (np.ndarray[N]): Массив предсказанных значений для каждой строки из data
        """
        cls._check_settings()
        # Прочитаем конфигурацию датасета
        dataset_config = cls.get_dataset_config(dataset_name)
        # Получим путь до сохранённой модели
        model_path = Path(cls.weights_root, dataset_name)
        if not model_path.exists():
            raise FileNotFoundError(f"No found trained model for '{dataset_name}' dataset by path {model_path}")
        # Сделаем предсказание
        result = predict(
            data,
            task=dataset_config['task'],
            weight_path=model_path
        )
        return result

    @classmethod
    def run_train(
            cls,
            dataset_name: str,
            time_limit: float = 5,
    ) -> dict[str, Any]:
        """
        Обучение модели на `dataset_name` наборе данных

        Args:
            dataset_name (str): Имя набора данных
            time_limit (float): Максимально допустимое время (в минутах) для поиска оптимального решения

        Returns:
            (dict[str, any]): Словарь с информацией о модели и её метриках
        """
        cls._check_settings()
        # Получим путь до набора данных
        data_path = cls.get_dataset_path(dataset_name)
        # Прочитаем конфигурацию датасета
        dataset_config = cls.get_dataset_config(dataset_name)
        # Сформируем путь для сохранения модели
        save_model_path = Path(cls.weights_root, dataset_name)
        # Запустим обучение
        model_info = train(
            data_path=Path(data_path, dataset_config['train_dataset']),
            task=dataset_config['task'],
            target_columns=dataset_config['target_columns'],
            index_col=dataset_config.get('index_col'),
            save_model_path=save_model_path,
            timeout=time_limit,
            if_exist='best'
        )
        model_info['pipeline']['nodes'] = [str(node) for node in model_info['pipeline']['nodes']]
        return model_info
