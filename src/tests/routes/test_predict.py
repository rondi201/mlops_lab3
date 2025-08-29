import numpy as np
import pytest
from fastapi import status


class TestPredictionEndpoints:
    """Тестовые случаи для ручек предсказания."""

    def test_predict_with_valid_file(
        self,
        test_client,
        correct_predict_input_data,
        correct_predict_output_predictions,
    ):
        """Тестирование POST /api/mlmodels/{mlmodel_id}/predict/"""
        mlmodel_id = 1

        files = {"data_file": ("test.csv", correct_predict_input_data, "text/csv")}
        response = test_client.post(f"/api/mlmodels/{mlmodel_id}/predict/", files=files)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert set(data.keys()) == {"mlmodel", "predicted_at", "predictions"}
        assert set(data["mlmodel"].keys()) == {"id", "name"}
        assert isinstance(data["predictions"], list)

        # Сравним допустимость отклонения предсказаний ответа (от API) и зафиксированных (из тестов модели) до 5%
        responce_prediction = np.array(data["predictions"])
        true_prediction = np.array(correct_predict_output_predictions)
        assert np.allclose(responce_prediction, true_prediction, rtol=0.05)

    def test_predict_with_invalid_file(self, test_client, mock_csv_file_bytes):
        """Тестирование POST /api/mlmodels/{mlmodel_id}/predict/ с некорректным файлом."""
        invalid_mlmodel_id = 1

        files = {"data_file": ("test.csv", mock_csv_file_bytes, "text/csv")}
        response = test_client.post(
            f"/api/mlmodels/{invalid_mlmodel_id}/predict/", files=files
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "message" in data

    def test_predict_with_invalid_model_id(
        self, test_client, correct_predict_input_data
    ):
        """Тестирование POST /api/mlmodels/{mlmodel_id}/predict/ с несуществующим ID."""
        invalid_mlmodel_id = 999

        files = {"data_file": ("test.csv", correct_predict_input_data, "text/csv")}
        response = test_client.post(
            f"/api/mlmodels/{invalid_mlmodel_id}/predict/", files=files
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "message" in data

    def test_predict_without_file(self, test_client):
        """Тестирование POST /api/mlmodels/{mlmodel_id}/predict/ без файла."""
        mlmodel_id = 8

        response = test_client.post(f"/api/mlmodels/{mlmodel_id}/predict/", data={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_predict_with_invalid_file_type(self, test_client):
        """Тестирование POST /api/mlmodels/{mlmodel_id}/predict/ c некорректным типом файла."""
        mlmodel_id = 1

        # Отправим не CSV файл
        files = {"data_file": ("test.txt", b"invalid content", "text/plain")}
        response = test_client.post(f"/api/mlmodels/{mlmodel_id}/predict/", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "message" in data
