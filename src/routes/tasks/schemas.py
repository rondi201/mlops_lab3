from pydantic import BaseModel, Field


class BasePredictTask(BaseModel):
    """
    Базовая схема для типов задачи.
    """

    id: int = Field(description="Идентификатор типа задачи", examples=[0])
    """ Идентификатор типа задачи """
    name: str = Field(description="Название типа задачи", examples=["classification"])
    """ Название типа задачи """
    title: str = Field(description="Человекочитаемое название типа задачи")
    """ Человекочитаемое название типа задачи """
