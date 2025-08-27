import io
import json
from typing import Any, BinaryIO, Generator
import tempfile

import pytest
import pandas as pd
from fastapi.testclient import TestClient

# Имортируем главное FastAPI приложение
from src.api import app
from src.utils import read_yaml


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    """Получение тестового клиента для приложения"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def correct_predict_input_data() -> Generator[BinaryIO, None, None]:
    """Получение правильного входного файла для тестирования предсказания"""
    with open("data/tests/datasets/test/test.csv", "rb") as file:
        yield file


@pytest.fixture
def correct_predict_output_predictions() -> dict[str, Any]:
    """Получение правильного выхода предсказания на тестовый вход из `correct_predict_input_data`"""
    output = read_yaml(
        "data/tests/weights/test_2025-08-22_18-33-47/output_test_prediction.yaml"
    )

    return output["predictions"]


@pytest.fixture
def mock_csv_file_bytes() -> BinaryIO:
    """Создание mock CSV файла для тестирования предсказания."""
    data = {
        "feature1": [1.0, 2.0, 3.0],
        "feature2": [4.0, 5.0, 6.0],
        "feature3": [7.0, 8.0, 9.0],
    }
    df = pd.DataFrame(data)

    # Convert to bytes
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer
    # csv_bytes = df.to_csv(index=False).encode("utf-8")
    # return io.BytesIO(csv_bytes)
