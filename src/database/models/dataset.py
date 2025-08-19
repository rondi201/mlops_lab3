from typing import TYPE_CHECKING
from dataclasses import dataclass

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from .base import Base

if TYPE_CHECKING:
    from .task import PredictTask


@dataclass
class Dataset(Base):
    """Класс-схема таблицы наборов данных"""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    """ Идентификатор набора данных """
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    """ Системное название набора данных """
    # title: Mapped[str] = mapped_column(String(128))
    # """ Человекочитаемое название набора данных """
    # description: Mapped[str] = mapped_column(String(512))
    # """ Человекочитаемое описание набора данных """
    task_id: Mapped[int] = mapped_column(ForeignKey("predict_tasks.id"))
    """ Идентификатор задачи """
    target_column: Mapped[str] = mapped_column(String(50))
    """  Название целевой колонки """
    index_column: Mapped[str | None] = mapped_column(String(50), nullable=True)
    """ Название колонки индекса """

    task: Mapped["PredictTask"] = relationship(
        lazy="selectin"  # Загрузка информации о задачи вместе с запросом
    )
    """ Информация о задачи """
