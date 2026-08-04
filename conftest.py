from automation.utils.logger import get_logger


def pytest_sessionstart(session):
    logger = get_logger()
    logger.info("Test execution started")
