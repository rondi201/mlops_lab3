from typing import Annotated

from fastapi import Depends
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from .schemas import DatasetInfo
from ... import dependencies
from ...database.models import Dataset
from ...database.repository import DatabaseRepository, ModelRepository
from ...schemas import Message

router = APIRouter()

DependDatabaseRepository = Annotated[
    DatabaseRepository, Depends(dependencies.get_database_repository)
]


@router.get(
    "/",
    response_model=list[DatasetInfo],
)
async def get_all_datasets_route(db_repository: DependDatabaseRepository):
    """Получение информации о всех наборах данных"""
    result = await db_repository.for_model(Dataset).get_all()

    return result


@router.get(
    "/{dataset_id}",
    response_model=DatasetInfo,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": Message,
            "description": "The item was not found.",
        }
    },
)
async def get_dataset_route(dataset_id: int, db_repository: DependDatabaseRepository):
    """Получение информации о конкретном наборе данных"""
    result = await db_repository.for_model(Dataset).get(dataset_id)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Item not found."},
        )

    return result
