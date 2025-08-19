from pydantic import BaseModel, Field


class HealthInfo(BaseModel):
    """
    Информация о состоянии сервера.
    """

    mem: str = Field(description="Количество используемой оперативной памяти", examples=["1.23 MiB"])
    """ Количество используемой оперативной памяти """
    cpu_usage: float = Field(description="Процент использования процессора", examples=[5.67])
    """ Процент использования процессора """
    threads: int = Field(description="Количество запущенных потоков", examples=[12])
    """ Количество запущенных потоков """


class HealthResponse(BaseModel):
    """
    Ответ на запрос состояния сервера.
    """

    status: str = Field("OK", description="Статус сервера")
    """ Статус сервера """
    info: HealthInfo = Field(description="Информация о состоянии сервера")
    """ Информация о состоянии сервера """
