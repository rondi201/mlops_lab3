# tests/test_mlmodels.py
import pytest
from fastapi import status


class TestMLModelEndpoints:
    """Тестовые случаи для /mlmodels"""

    def test_get_all_mlmodels(self, test_client):
        """Тестирование GET /api/mlmodels/"""
        response = test_client.get("/api/mlmodels/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        if data:
            model = data[0]
            assert set(model.keys()) == {
                "id",
                "name",
                "title",
                "description",
                "dataset_id",
                "trained_at",
            }

    def test_get_mlmodel_by_id_success(self, test_client):
        """Тестирование GET /api/mlmodels/{mlmodel_id}"""
        mlmodel_id = 1
        response = test_client.get(f"/api/mlmodels/{mlmodel_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == mlmodel_id
        assert set(data.keys()) == {
            "id",
            "name",
            "title",
            "description",
            "dataset_id",
            "trained_at",
        }

    def test_get_mlmodel_by_id_not_found(self, test_client):
        """Тестирование GET /api/mlmodels/{mlmodel_id}  с несуществующим ID"""
        non_existent_id = 999

        response = test_client.get(f"/api/mlmodels/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "message" in data

    def test_get_mlmodel_by_id_invalid_type(self, test_client):
        """Тестирование GET /api/mlmodels/{mlmodel_id}  c некорректным типом ID"""
        invalid_id = "invalid"

        response = test_client.get(f"/api/mlmodels/{invalid_id}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
