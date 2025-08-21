import datetime
from pydantic import BaseModel, Field


class BaseMLModel(BaseModel):
    """
    Базовая схема для ML моделей.
    """

    id: int = Field(description="Идентификатор ML модели", examples=[8])
    """ Идентификатор ML модели """
    name: str = Field(description="Название ML модели", examples=["iris_model"])
    """ Название ML модели """


class MLModelInfo(BaseMLModel):
    """
    Информация о ML модели.
    """

    title: str = Field(description="Человекочитаемое название ML модели")
    """ Человекочитаемое название ML модели """
    description: str = Field(description="Человекочитаемое описание ML модели")
    """ Человекочитаемое описание ML модели """
    dataset_id: int = Field(
        description="Идентификатор набора данных, на котором обучалась модель",
        examples=[12],
    )
    """  Идентификатор набора данных, на котором обучалась модель """
    trained_at: datetime.datetime = Field(
        description="Время когда модель была обучена",
        examples=[datetime.datetime(2023, 1, 1, 12, 5).isoformat()],
    )
    """ Время когда модель была обучена """
