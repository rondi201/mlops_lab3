from typing import Generic, Sequence, TypeVar

from sqlalchemy import (
    ColumnElement,
    BinaryExpression,
    select,
)
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.orm.interfaces import ORMOption
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError

from . import models

Model = TypeVar("Model", bound=models.Base)


class DatabaseRepository:
    """Репозиторий для работы с базой данных"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def for_model(self, model: type[Model]) -> "ModelRepository[Model]":
        """Возвращает репозиторий для указанной модели"""
        return ModelRepository(model, session=self.session)

    async def ping(self):
        """Проверка подклюения к базе данных (ping)"""
        try:
            await self.session.scalar(select(1))
        except Exception as e:
            raise ConnectionError(
                f"Couldn't connect to the database. Reason: ({type(e)}) {e}"
            ).with_traceback(e.__traceback__)


class ModelRepository(Generic[Model]):
    """Репозиторий для управления сущностями базы данных."""

    def __init__(self, model: type[Model], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    def _get_instance_from_data(self, data: dict | Model) -> Model:
        """Получение объекта модели из различных источников"""
        if isinstance(data, models.Base):
            if isinstance(data, self.model):
                return data
            else:
                raise ValueError(
                    f"Given model entity in data must be instance of {self.model.__class__.__name__}"
                    f"got instance of {type(data).__class__.__name__}"
                )
        return self.model(**data)

    async def create(self, data: dict | Model, auto_commit: bool = True) -> Model:
        """Создать запись сущности в таблице базы данных"""
        instance = self._get_instance_from_data(data=data)
        self.session.add(instance)
        if auto_commit:
            await self.session.commit()
            await self.session.refresh(instance)
        return instance

    async def update(self, data: dict | Model, auto_commit: bool = True) -> Model:
        """Обновить запись сущности в таблице базы данных, если задан primary key, иначе создать новую"""
        instance = self._get_instance_from_data(data=data)
        instance = await self.session.merge(instance)
        if auto_commit:
            await self.session.commit()
            await self.session.refresh(instance)
        return instance

    async def get(
        self,
        pk: str | int,
        with_relationships: Sequence[InstrumentedAttribute] | None = None,
    ) -> Model | None:
        """
        Получить сущность на основе первичного ключа

        Args:
            pk (str | int): первичный ключ модели
            with_relationships (Sequence[InstrumentedAttribute] | None): Список связанных моделей вида
                `Model.relationship_field` для совместной загрузки в рамках политики `selectinload`.
                Позволяет подгрузить связанные сущности сразу и избежать отложенной загрузки.

        Returns:
            Model | None: Сущность модели
        """
        options: list[ORMOption] = []
        # Если переданы связанные модели - добавим их загрузку как `selectinload` в `options`
        if with_relationships:
            for relship in with_relationships:
                options.append(selectinload(relship))

        return await self.session.get(self.model, pk, options=options)

    async def get_all(
        self,
        *expressions: BinaryExpression | ColumnElement,
        with_relationships: Sequence[InstrumentedAttribute] | None = None,
    ) -> list[Model]:
        """
        Получить все записи сущности

        Args:
            *expressions (ColumnElement | BinaryExpression): параметры фильтрации вида `Model.name == 'foo'`
            with_relationships (Sequence[InstrumentedAttribute] | None): Список связанных моделей вида
                `Model.relationship_field` для совместной загрузки в рамках политики `selectinload`.
                Позволяет подгрузить связанные сущности сразу и избежать отложенной загрузки.

        Returns:
            list[Model]: список найденных cущностей модели
        """
        options: list[ExecutableOption] = []
        # Если переданы связанные модели - добавим их загрузку как `selectinload` в `options`
        if with_relationships:
            for relship in with_relationships:
                options.append(selectinload(relship))

        query = select(self.model)
        if expressions:
            query = query.where(*expressions)
        if options:
            query.options(*options)

        return list(await self.session.scalars(query))

    async def exsist(
        self,
        *expressions: BinaryExpression,
    ) -> bool:
        """
        Проверка, существуюет ли запись в базе подходящая под условия

        Args:
            *expressions (BinaryExpression): параметры фильтрации вида `Model.name == 'foo'`

        Returns:
            bool: существуют ли записи в базе, подходящие под данные условия
        """
        query = select(self.model).where(*expressions).exists()
        is_exist = bool(  # Убираем ошибку типизации bool | None
            await self.session.scalar(select(query))
        )
        return is_exist
