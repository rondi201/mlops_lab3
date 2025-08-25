import asyncio
import datetime
from logging import Logger
from typing import Annotated

from fastapi import Depends, File, Path, UploadFile
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter


from .schemas import PredictOutput
from .service import PredictService
from ... import dependencies
from ...database.models import MLModel
from ...database.repository import DatabaseRepository, ModelRepository
from ...schemas import Message

router = APIRouter()

DependDatabaseRepository = Annotated[
    DatabaseRepository, Depends(dependencies.get_database_repository)
]
DependLogger = Annotated[Logger, Depends(dependencies.get_app_logger)]


@router.post(
    "/",
    tags=["Predict"],
    response_model=PredictOutput,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": Message,
            "description": "The ML model was not found",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": Message,
            "description": "The uploaded file was incorrect",
        },
    },
)
async def get_model_prediction_route(
    db_repository: DependDatabaseRepository,
    mlmodel_id: Annotated[
        int, Path(description="Идентификатор ML модели", examples=[8])
    ],
    data_file: UploadFile = File(
        description="Файл формата .csv, содержащий столбцы признаков из обучающего набора данных."
    ),
):
    """
    Предсказание данных из `data_file`файла моделью, обученной на `dataset_name` наборе данных.
    """
    # Загрузим сущность модели вместе с набором данных
    ml_model = await db_repository.for_model(MLModel).get(
        mlmodel_id, with_relationships=[MLModel.dataset]
    )
    # Если сущность не найдена
    if ml_model is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "ML model with id {mlmodel_id} not found."},
        )
    # Загрузим данные
    try:
        # Воспользуемся asyncio.to_thread для вынесения ресурсоемких задач в отдельный поток
        data = await asyncio.to_thread(PredictService.load_data_from_file, data_file)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Reading the uploaded file caused an error. "
                "Check the file format and the integrity of the content."
            },
        )
    # Проверим длину файла
    if data.shape[0] == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "No found any row in uploaded data file."},
        )
    # Предобработаем данные
    try:
        # Воспользуемся asyncio.to_thread для вынесения ресурсоемких задач в отдельный поток
        prepared_data = await asyncio.to_thread(
            PredictService.prepare_data_for_prediction, data, ml_model
        )
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Preparing the uploaded file caused an error. "
                "Check correctness of column titles, cell types and whether this data belongs "
                f"to the training dataset with title '{ml_model.dataset.title}'.",
            },
        )
    # Получим предсказания от модели
    # Воспользуемся asyncio.to_thread для вынесения ресурсоемких задач в отдельный поток
    result_array = await asyncio.to_thread(
        PredictService.get_predict, prepared_data, ml_model
    )

    return {
        "mlmodel": ml_model,
        "predicted_at": datetime.datetime.now(),
        "predictions": result_array.tolist(),
    }
