import logging
from logging.handlers import TimedRotatingFileHandler


def setup_logging(log_file_path: str = "/logs/bot.log"):
    """
    Настраивает логирование с ротацией логов по дате.

    :param log_file_path: Путь к файлу логов.
    """
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    log_handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1)
    log_handler.suffix = "%Y-%m-%d"
    log_handler.setFormatter(log_formatter)

    # Логгер для записи в файл
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    # Логгер для вывода в консоль (по желанию)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logger.info("Логирование настроено.")