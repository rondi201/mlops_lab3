from pydantic import BaseModel, Field


class BasePredictTask(BaseModel):
    """
    Базовая схема для наборов данных.
    """

    id: int = Field(description="Идентификатор типа задачи", examples=[0])
    """ Идентификатор набора данных """
    name: str = Field(description="Название типа задачи", examples=["classification"])
    """ Название набора данных """
