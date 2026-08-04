import logging
import os
from datetime import datetime


def get_logger():

    log_folder = "reports/logs"

    os.makedirs(log_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    log_file = f"{log_folder}/execution_{timestamp}.log"

    logger = logging.getLogger("automation")

    logger.setLevel(logging.INFO)

    # avoid duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger
