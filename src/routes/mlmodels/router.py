from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from .schemas import MLModelInfo
from ... import dependencies
from ...schemas import Message
from ...database.models import MLModel
from ...database.repository import DatabaseRepository, ModelRepository

router = APIRouter()

DependDatabaseRepository = Annotated[
    DatabaseRepository, Depends(dependencies.get_database_repository)
]


@router.get("/", response_model=list[MLModelInfo])
async def get_all_mlmodels_route(db_repository: DependDatabaseRepository):
    """Получение информации о всех наборах данных"""
    result = await db_repository.for_model(MLModel).get_all()

    return result


@router.get(
    "/{mlmodel_id}",
    response_model=MLModelInfo,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": Message,
            "description": "The item was not found.",
        }
    },
)
async def get_mlmodel_route(mlmodel_id: int, db_repository: DependDatabaseRepository):
    """Получение информации о конкретном наборе данных"""
    result = await db_repository.for_model(MLModel).get(mlmodel_id)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Item not found."},
        )

    return result
