from pydantic import BaseModel, Field


class BaseDataset(BaseModel):
    """
    Базовая схема для наборов данных.
    """

    id: int = Field(description="Идентификатор набора данных", examples=[12])
    """ Идентификатор набора данных """
    name: str = Field(description="Название набора данных", examples=["iris"])
    """ Название набора данных """


class DatasetInfo(BaseDataset):
    """
    Информация о наборе данных.
    """

    target_column: str = Field(
        description="Название целевой колонки", examples=["target"]
    )
    """  Название целевой колонки """
    index_column: str | None = Field(
        default=None, description="Имя колонки индекса", examples=["index"]
    )
    """ Имя колонки индекса """
    task_id: int = Field(description="Идентификатор задачи", examples=[1])
    """ Идентификатор задачи """
