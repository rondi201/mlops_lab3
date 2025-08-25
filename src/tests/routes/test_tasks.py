import pytest
from fastapi import status


class TestTaskEndpoints:
    """Тестовые случаи для ручки /tasks"""

    def test_get_all_tasks(self, test_client):
        """Тестирование GET /api/tasks/"""
        response = test_client.get("/api/tasks/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        if data:
            task = data[0]
            assert set(task.keys()) == {"id", "name", "title"}

    def test_get_task_by_id_success(self, test_client):
        """Тестирование GET /api/tasks/{task_id} с корректным ID"""
        task_id = 1
        response = test_client.get(f"/api/tasks/{task_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == task_id
        assert set(data.keys()) == {"id", "name", "title"}

    def test_get_task_by_id_not_found(self, test_client):
        """Тестирование GET /api/tasks/{task_id} с несуществующим ID"""
        non_existent_id = 999

        response = test_client.get(f"/api/tasks/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "message" in data

    def test_get_task_by_id_invalid_type(self, test_client):
        """Тестирование GET /api/tasks/{task_id} c некорректным типом ID"""
        invalid_id = "invalid"

        response = test_client.get(f"/api/tasks/{invalid_id}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
