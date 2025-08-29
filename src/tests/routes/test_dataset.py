import pytest
from fastapi import status


class TestDatasetEndpoints:
    """Тестовые случаи для ручки /datasets"""

    def test_get_all_datasets(self, test_client):
        """Тестирование GET /api/datasets/"""
        response = test_client.get("/api/datasets/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        if data:
            dataset = data[0]
            assert set(dataset.keys()) == {
                "id",
                "name",
                "title",
                "description",
                "target_column",
                "index_column",
                "task_id",
            }

    def test_get_dataset_by_id_success(self, test_client):
        """Тестирование GET /api/datasets/{dataset_id} с корректным ID"""
        dataset_id = 1
        response = test_client.get(f"/api/datasets/{dataset_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == dataset_id
        assert set(data.keys()) == {
            "id",
            "name",
            "title",
            "description",
            "target_column",
            "index_column",
            "task_id",
        }

    def test_get_dataset_by_id_not_found(self, test_client):
        """Тестирование GET /api/datasets/{dataset_id} с несуществующим ID"""
        non_existent_id = 999

        response = test_client.get(f"/api/datasets/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "message" in data

    def test_get_dataset_by_id_invalid_type(self, test_client):
        """Тестирование GET /api/datasets/{dataset_id} c некорректным типом ID"""
        invalid_id = "invalid"

        response = test_client.get(f"/api/datasets/{invalid_id}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
