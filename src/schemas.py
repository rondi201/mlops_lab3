"""Глобальные схемы сообщений для FastAPI"""

from pydantic import BaseModel


class Message(BaseModel):
    """Базовая структура сообщений об ошибках и информационных сообщений"""

    message: str
