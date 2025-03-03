import shutil
import unittest
from pathlib import Path

import pandas as pd

from src.api_methods import APIMethods
from src.config import api_config
from copy import deepcopy
from src.utils import read_yaml

# Отключим сортировку тестов, чтобы они шли последовательно для сохранения состояния между train и predict
unittest.TestLoader.sortTestMethodsUsing = None


class APIMethodsTest(unittest.TestCase):
    datasets_root = 'data/tests/datasets'
    weights_root = 'data/tests/weights'
    test_dataset_name = 'test'

    @classmethod
    def setUpClass(cls) -> None:
        config = deepcopy(api_config)
        config['datasets_root'] = cls.datasets_root
        config['weights_root'] = cls.weights_root
        APIMethods.setting(
            **config
        )

    # ------------- Протестируем работ с наборами данных ---------------
    def test_get_dataset_names(self):
        self.assertEqual(APIMethods.get_dataset_names(), [self.test_dataset_name])

    def test_get_dataset_config(self):
        # Считаем конфиг тестового набора данных
        dataset_config = read_yaml(Path(self.datasets_root, self.test_dataset_name, 'config.yaml'))
        self.assertEqual(APIMethods.get_dataset_config(self.test_dataset_name), dataset_config)

    def test_get_dataset_configs(self):
        # Считаем конфиг тестового набора данных
        dataset_config = read_yaml(Path(self.datasets_root, self.test_dataset_name, 'config.yaml'))
        self.assertEqual(APIMethods.get_dataset_configs(), {self.test_dataset_name: dataset_config})

    # ------------- Проверим работу обучения модели ---------------------

    def test_train_model(self):
        save_path = Path(self.weights_root, self.test_dataset_name)
        if save_path.exists():
            shutil.rmtree(save_path)

        model_info = APIMethods.run_train(self.test_dataset_name, time_limit=0.1)
        self.assertEqual(model_info['save'], True)

    # ------------ Проверим работу предсказания модели -------------------

    def test_predict_model(self):
        data_path = Path(self.datasets_root, self.test_dataset_name, 'test.csv')
        data = pd.read_csv(data_path)
        predict = APIMethods.get_predict(data, self.test_dataset_name)
        self.assertEqual(len(predict), len(data))

    @classmethod
    def tearDownClass(cls) -> None:
        save_path = Path(cls.weights_root, cls.test_dataset_name)
        if save_path.exists():
            shutil.rmtree(save_path)


if __name__ == "__main__":
    unittest.main()
