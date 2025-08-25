import asyncio
from typing import Annotated

from fastapi import Depends
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from .schemas import BasePredictTask
from ... import dependencies
from ...database.models import PredictTask
from ...database.repository import DatabaseRepository, ModelRepository
from ...schemas import Message

router = APIRouter()

DependDatabaseRepository = Annotated[
    DatabaseRepository, Depends(dependencies.get_database_repository)
]


@router.get(
    "/",
    response_model=list[BasePredictTask],
)
async def get_all_datasets_route(db_repository: DependDatabaseRepository):
    """Получение информации о всех типах задачи"""
    result = await db_repository.for_model(PredictTask).get_all()

    return result


@router.get(
    "/{task_id}",
    response_model=BasePredictTask,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": Message,
            "description": "The item was not found.",
        }
    },
)
async def get_dataset_route(task_id: int, db_repository: DependDatabaseRepository):
    """Получение информации о конкретном типе задачи"""
    model_feature = db_repository.for_model(PredictTask).get(task_id)
    # Запускаем асинхронную функцию в синхронном коде
    result = await model_feature
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Item not found."},
        )

    return result
