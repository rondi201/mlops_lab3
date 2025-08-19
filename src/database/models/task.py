from dataclasses import dataclass

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from .base import Base


@dataclass
class PredictTask(Base):
    """Класс-схема таблицы задач предсказания"""

    __tablename__ = "predict_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    """ Идентификатор задачи """
    name: Mapped[str] = mapped_column(String(50))
    """ Системное название задачи """
    # title: Mapped[str] = mapped_column(String(128))
    # """ Человекочитаемое название метрики """
