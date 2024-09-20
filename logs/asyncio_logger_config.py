import os
import logging
from logging.handlers import TimedRotatingFileHandler

from aiologger.formatters.json import JsonFormatter
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler


class AsyncLoggerSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_file_path):
        self._logger = None
        self.log_file_path = log_file_path

    async def get_logger(self):
        if self._logger is None:
            self._logger = await self.setup_logging(self.log_file_path)
        return self._logger

    @staticmethod
    async def setup_logging(log_file_path: str):
        log_formatter = UnicodeDecodingJsonFormatter()

        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        aiogram_logger = Logger(name="aiogram", level="INFO")

        file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1)
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(log_formatter)

        logging.getLogger("aiogram").addHandler(file_handler)

        console_handler = AsyncStreamHandler()
        console_handler.formatter = log_formatter

        aiogram_logger.add_handler(console_handler)

        return aiogram_logger

class UnicodeDecodingJsonFormatter(JsonFormatter):
    def format(self, record):
        if isinstance(record.msg, str):
            try:
                record.msg = bytes(record.msg, 'utf-8').decode('unicode_escape')
            except Exception as e:
                record.msg = f"Ошибка декодирования: {e}"
        return super().format(record)