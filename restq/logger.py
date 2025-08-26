import logging
from typing import Optional
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class LoggerService:
    LOG_FORMAT_DEBUG = "[RESTQ] %(process)d - %(asctime)s    LEVEL:[%(levelname)s] %(name)s %(message)s"

    LEVEL_COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA + Style.BRIGHT,
    }

    class ColorFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            level_color = LoggerService.LEVEL_COLORS.get(record.levelname, "")
            record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
            record.name = f"{Fore.LIGHTBLUE_EX}{record.name}{Style.RESET_ALL}"
            return super().format(record)

    def __init__(self) -> None:
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)

        formatter = LoggerService.ColorFormatter(
            self.LOG_FORMAT_DEBUG,
            datefmt="%m/%d/%Y, %I:%M:%S %p"
        )
        self.console_handler.setFormatter(formatter)

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if not logger.hasHandlers():
            logger.addHandler(self.console_handler)

        # Optional: suppress noisy libraries
        for noisy_logger in ["botocore", "boto3", "urllib3", "s3transfer"]:
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)

        return logger
    

logger = LoggerService().get_logger("RestQ Logger")

