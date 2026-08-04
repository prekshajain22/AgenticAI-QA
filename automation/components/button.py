from time import sleep

from automation.components.base_component import BaseComponent
from config.settings import DEFAULT_TIMEOUT


class Button(BaseComponent):
    def click(self, retries=2, timeout=DEFAULT_TIMEOUT):

        for attempt in range(retries + 1):
            try:
                self.wait_until_visible(timeout)
                self.logger.info(f"Clicking '{self.name}' ({attempt + 1}/{retries + 1})")
                self.locator.click()
                self.logger.info("Button clicked successfully")
                return
            except Exception as error:
                self.logger.warning(f"Click failed: {error}")
                if attempt == retries:
                    self.logger.error("Button click failed after retries")
                    raise
                sleep(0.5)

    def double_click(self):
        self.wait_until_visible()
        self.logger.info(f"Double-clicking '{self.name}'")
        self.locator.dblclick()

    def right_click(self):
        self.wait_until_visible()
        self.logger.info(f"Right-clicking '{self.name}'")
        self.locator.click(button="right")

    def is_enabled(self):
        self.logger.info(f"Checking '{self.name}' is enabled")
        return self.locator.is_enabled()

    def is_disabled(self):
        self.logger.info(f"Checking '{self.name}' is disabled")
        return self.locator.is_disabled()
