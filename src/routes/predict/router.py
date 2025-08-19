import datetime
from logging import Logger
from typing import Annotated

from fastapi import Depends, File, UploadFile
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter


from .schemas import PredictInput, PredictOutput
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
        status.HTTP_400_BAD_REQUEST: {
            "model": Message,
            "description": "The ML model was not found or the uploaded file was uncorrect",
        }
    },
)
async def get_model_prediction_route(
    db_repository: DependDatabaseRepository,
    predict_input: PredictInput,
    data_file: UploadFile = File(
        description="Файл формата .csv, содержащий столбцы признаков из обучающего набора данных."
    ),
):
    """
    Предсказание данных из `data_file`файла моделью, обученной на `dataset_name` наборе данных.
    """
    # Загрузим сущность модели вместе с набором данных
    ml_model = await db_repository.for_model(MLModel).get(
        predict_input.mlmodel_id, with_relationships=[MLModel.dataset]
    )
    # Если сущность не найдена
    if ml_model is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "ML model with id {predict_input.mlmodel_id} not found."
            },
        )
    # Загрузим данные
    try:
        data = PredictService.load_data_from_file(data_file)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Reading the uploaded file caused an error. "
                "Check the file format and the integrity of the content."
            },
        )
    # Получим предсказания от модели
    result_array = PredictService.get_predict(data, ml_model)

    return {
        "mlmodel": ml_model,
        "predicted_at": datetime.datetime.now(),
        "predictions": result_array.tolist(),
    }
