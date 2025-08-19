from functools import cache
import os

# import hydra
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    """Настройки запуска приложения"""

    host: str = "localhost"
    """ Имя хоста для доступа к приложению """
    port: int = 8000
    """ Порт для доступа к приложению """


class StorageConfig(BaseModel):
    """Настройки путей для хранения объектов"""

    datasets_root: str = "data/datasets"
    weights_root: str = "data/weights"


class SeedingConfig(BaseModel):
    """Настройки автозаполнения базы данных"""

    predict_tasks_seeding_config: str = "data/seed_data/predict_task.json"


class ApiPrefixConfig(BaseModel):
    """Настройки путей для доступа к routers"""

    prefix: str = "/api"
    health: str = "/health"
    datasets: str = "/datasets"
    mlmodels: str = "/mlmodels"
    predict: str = "/predict"
    tasks: str = "/tasks"


class DatabaseConfig(BaseModel):
    """Конфигурация настройки базы данных"""

    dialect: str = ""
    """ Вид диалекта SQL (см. https://docs.sqlalchemy.org/en/20/core/engines.html) """
    host: str = "localhost"
    """ Адрес базы данных """
    port: int = 5432
    """ Порт базы данных """
    user: str = "su"
    """ Логин для доступа к базе данных """
    password: SecretStr = SecretStr("")
    """ Пароль для доступа к базе данных """
    database: str = ""
    """ Имя базы в базе данных """


class Settings(BaseSettings):
    """Модель настройки приложения"""

    model_config = SettingsConfigDict(
        env_file=os.getenv("APP_ENV_FILE", ".env"),
        extra="ignore",  # Игнорирование посторонних переменных
        case_sensitive=False,
        env_nested_delimiter="__",
        # env_nested_max_split=1,  # Максимальная вложенность настроек - 2
    )
    run: RunConfig = RunConfig()
    api: ApiPrefixConfig = ApiPrefixConfig()
    db: DatabaseConfig = DatabaseConfig()
    storage: StorageConfig = StorageConfig()
    seeding: SeedingConfig = SeedingConfig()


class ConfigManager:
    """
    Класс для получения конфигураций различных частей приложения

    Обёртка над BaseSettings без необходимости создания экземпляра класса настроек сразу,
    что позволяет исбежать ошибок, если происходит импорт компонента без потенциального запуска приложения.
    """

    APP_ENV_PREFIX: str = "APP_"

    @cache
    def get_settings(self) -> Settings:
        """Получить полные настройки приложения"""
        Settings.model_config
        return Settings(_env_prefix=self.APP_ENV_PREFIX)  # type: ignore

    @property
    def api_config(self) -> ApiPrefixConfig:
        return self.get_settings().api

    @property
    def run_config(self) -> RunConfig:
        return self.get_settings().run

    @property
    def db_config(self) -> DatabaseConfig:
        return self.get_settings().db

    @property
    def storage_config(self) -> StorageConfig:
        return self.get_settings().storage

    @property
    def seeding_config(self) -> SeedingConfig:
        return self.get_settings().seeding


config_manager = ConfigManager()
