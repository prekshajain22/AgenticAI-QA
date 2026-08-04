from automation.utils.logger import get_logger
from automation.utils.waits import Waits


class BaseComponent:
    def __init__(self, page, locator, name=None):
        self.page = page
        self.locator = page.locator(locator)
        self.name = name or locator
        self.logger = get_logger()

    def wait_until_visible(self, timeout=Waits.DEFAULT_TIMEOUT):
        Waits.until_visible(self.locator, timeout)

    def is_visible(self):
        self.logger.info(f"Verifying '{self.name}' is visible")
        return self.locator.is_visible()
