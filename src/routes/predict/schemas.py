import datetime
from pydantic import BaseModel, Field
from ..mlmodels.schemas import BaseMLModel


class PredictOutput(BaseModel):
    """Выходные данные от предсказания"""

    mlmodel: BaseMLModel = Field(
        description="Информация об ML модели, использовавшейся для предсказания"
    )
    """ML модель"""

    predicted_at: datetime.datetime = Field(
        description="Время выполнения предсказания",
        examples=[datetime.datetime(2023, 1, 1, 12, 5).isoformat()],
    )
    """Время выполнения предсказания"""
    predictions: list[float | int] = Field(
        description="Список предсказаний целевого атрибута. Формат зависимости от типа задачи \
            (float - регрессия, int - классификация). Порядок аналогичен порядку строк в переданных данных.",
        examples=[[0.15, 26.1, 72.5], [0, 1, 1, 2, 0]],
    )
    """Список предсказаний целевого атрибута"""
