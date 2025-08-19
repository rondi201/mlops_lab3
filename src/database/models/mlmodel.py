import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime

from .base import Base

if TYPE_CHECKING:
    from .dataset import Dataset


@dataclass
class MLModel(Base):
    """Класс-схема таблицы моделей"""

    __tablename__ = "mlmodels"

    id: Mapped[int] = mapped_column(primary_key=True)
    """ Идентификатор модели """
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    """ Системное название модели """
    # title: Mapped[str] = mapped_column(String(128))
    # """ Человекочитаемое название модели """
    # description: Mapped[str] = mapped_column(String(512))
    # """ Человекочитаемое описание модели """
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE")
    )
    """ Идентификатор набора данных, на котором обучена модель """
    trained_at: Mapped[datetime.datetime] = mapped_column(DateTime(), unique=True)
    """ Время когда модель была обучена """

    dataset: Mapped["Dataset"] = relationship(lazy="select")
    """ Информация о наборе данных, на котором обучена модель """
