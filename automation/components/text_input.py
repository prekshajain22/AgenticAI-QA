from automation.components.base_component import BaseComponent
from config.settings import DEFAULT_TIMEOUT


class TextInput(BaseComponent):
    def enter(self, value, timeout=DEFAULT_TIMEOUT, sensitive=False):
        self.wait_until_visible(timeout)
        display_value = "******" if sensitive else value
        self.logger.info(f"Entering '{display_value}' into '{self.name}'")
        self.locator.fill(value)

    def clear(self):
        self.wait_until_visible()
        self.logger.info(f"Clearing '{self.name}'")
        self.locator.clear()

    def append(self, value):
        self.wait_until_visible()
        self.logger.info(f"Appending '{value}' into '{self.name}'")
        self.locator.press_sequentially(value)

    def get_value(self):
        self.wait_until_visible()
        self.logger.info(f"Reading value from '{self.name}'")
        return self.locator.input_value()
