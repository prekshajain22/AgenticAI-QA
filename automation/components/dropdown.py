from automation.components.base_component import BaseComponent


class Dropdown(BaseComponent):
    def select(self, value):
        self.wait_until_visible()
        self.logger.info(f"Selecting '{value}' from '{self.name}'")
        self.locator.select_option(value)

    def selected_value(self):
        self.wait_until_visible()
        self.logger.info(f"Getting selected value from '{self.name}'")
        return self.locator.input_value()
