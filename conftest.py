from automation.utils.logger import get_logger


def pytest_sessionstart(session):
    logger = get_logger()
    logger.info("Test execution started")


pytest_plugins = [
    "automation.fixtures.browser_fixtures",
    "automation.fixtures.data_fixtures",
    "automation.fixtures.pages_fixtures",
    "automation.fixtures.action_fixtures",
    "automation.fixtures.screenshot_fixtures",
    "tests.step_definitions.shared_steps",
]
