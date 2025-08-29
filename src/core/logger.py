import logging
import os
import sys

from typing import Union, Optional
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path("log", "logfile.log")
DEBUG_LOG_FORMAT = (
    "[%(asctime)s] %(levelname)s (%(name)s - %(funcName)s:%(lineno)d): %(message)s"
)
INFO_LOG_FORMAT = "[%(asctime)s] %(levelname)s (%(name)s): %(message)s"


class LoggerFactory:
    """
    Class for logging behaviour of data exporting - object of ExportingTool class
    """

    log_level = logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
    )
    show = True
    in_file = False

    @classmethod
    def setting(
        cls,
        log_level: Union[str, int] = logging.INFO,  # type: ignore
        log_format: Optional[str] = None,
        show: bool = True,
        in_file: bool = False,
    ) -> None:
        """
            Re-defined __init__ method which sets show parametr

        Args:
            log_level (str, int): logging level as string or logging.<log level> (like logging.INFO)
            log_format: (str): logging format of saved massage
            show (bool): if set all logs will be shown in terminal
            in_file (bool): if set all logs will be written in file
        """
        if isinstance(log_level, str):
            log_level: int = logging.getLevelName(log_level)
        if log_format is None:
            log_format = (
                INFO_LOG_FORMAT if log_level > logging.DEBUG else DEBUG_LOG_FORMAT
            )
        cls.show = show
        cls.in_file = in_file
        cls.log_level = log_level
        cls.formatter = logging.Formatter(log_format)

    @classmethod
    def get_console_handler(cls) -> logging.StreamHandler:
        """
            Class method the aim of which is getting a console handler to show logs on terminal

        Returns:
            logging.StreamHandler: handler object for streaming output through terminal
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(cls.formatter)
        return console_handler

    @classmethod
    def get_file_handler(cls) -> logging.FileHandler:
        """
            Class method the aim of which is getting a file handler to write logs in file LOG_FILE

        Returns:
            logging.FileHandler: handler object for streaming output through std::filestream
        """
        file_handler = logging.FileHandler(LOG_FILE, mode="w")
        file_handler.setFormatter(cls.formatter)
        return file_handler

    @classmethod
    def get_logger(cls, logger_name: str) -> logging.Logger:
        """
            Class method which creates logger with certain name

        Args:
            logger_name (str): name for logger

        Returns:
            logger: object of Logger class
        """
        logger = logging.getLogger(logger_name)
        if logger.hasHandlers() and logger.handlers:
            return logger
        # Настроим параметры логгирования
        logger.setLevel(cls.log_level)
        if cls.show:
            logger.addHandler(cls.get_console_handler())
        if cls.in_file:
            logger.addHandler(cls.get_file_handler())
        logger.propagate = False
        return logger


# Настроим фабрику логгов
LoggerFactory.setting(
    log_level=LOG_LEVEL,
    show=True,
    in_file=False,
)
